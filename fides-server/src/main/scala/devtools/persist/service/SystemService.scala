package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.controller.RequestContext
import devtools.domain.{PrivacyDeclaration, Registry, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.systemQuery
import devtools.persist.db.Tables.SystemQuery
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.SystemValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class SystemService(
  daos: DAOs,
  val privacyDeclarationService: PrivacyDeclarationService,
  val validator: SystemValidator
)(implicit ec: ExecutionContext)
  extends AuditingService[SystemObject, SystemQuery](daos.systemDAO, daos.auditLogDAO, daos.organizationDAO, validator)
  with LazyLogging with UniqueKeySearch[SystemObject, SystemQuery] {

  override def hydrate(s: SystemObject): Future[SystemObject] =
    daos.privacyDeclarationDAO.filter(_.systemId === s.id).map(d => s.copy(privacyDeclarations = Some(d)))

  /** retrieve an org id from the base type */
  override def orgId(t: SystemObject): Long = t.organizationId

  /** actual create action that runs post validations, audit changes, and any other type-specific actions. */
  override def createAudited(record: SystemObject, versionStamp: Long, ctx: RequestContext): Future[SystemObject] = {
    for {
      s <- daos.systemDAO.create(record.copy(versionStamp = Some(versionStamp)))
      t <- record.privacyDeclarations match {
        case None => Future.successful(None)
        case Some(declarations) =>
          Future
            .sequence(
              declarations.map(fld => privacyDeclarationService.createValidated(fld.copy(systemId = s.id), ctx))
            )
            .map(t => Some(t))
      }
    } yield s.copy(privacyDeclarations = t)
  }

  /** actual update action that runs post validations, audit changes, and any other type-specific actions. */
  override def updateAudited(
    record: SystemObject,
    versionStamp: Long,
    previous: SystemObject,
    ctx: RequestContext
  ): Future[Option[SystemObject]] =
    for {
      updated: Option[SystemObject] <- dao.update(record.copy(versionStamp = Some(versionStamp)))
      _ = record.registryId.map(daos.registryDAO.setVersion(_, versionStamp))
      declarations <- record.privacyDeclarations match {

        case Some(ds) =>
          for {
            _ <- daos.privacyDeclarationDAO.delete(_.systemId === record.id)
            createdFields <- Future.sequence(ds.map { d: PrivacyDeclaration =>
              privacyDeclarationService.createValidated(d.copy(systemId = record.id), ctx)
            })
          } yield Some(createdFields)

        case None => Future.successful(None)
      }
    } yield updated.map(_.copy(privacyDeclarations = declarations))

  /** actual delete action that runs post validations, audit changes, and any other type-specific actions. */
  override def deleteAudited(id: Long, versionStamp: Long, previous: SystemObject, ctx: RequestContext): Future[Int] =
    for {
      deleted <- dao.delete(id)
      _ = previous.registryId.map(daos.registryDAO.setVersion(_, versionStamp))
    } yield deleted

  def findByUniqueKeyQuery(organizationId: Long, key: String): SystemQuery => Rep[Boolean] = { q =>
    q.fidesKey === key && q.organizationId === organizationId
  }

}
