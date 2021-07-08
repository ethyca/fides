package devtools.persist.service

import devtools.App.registryDAO
import devtools.controller.RequestContext
import devtools.domain.Registry
import devtools.persist.dao._
import devtools.persist.db.Tables.{RegistryQuery, systemQuery}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.RegistryValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class RegistryService(
  val daos: DAOs,
  val validator: RegistryValidator
)(implicit ec: ExecutionContext)
  extends AuditingService[Registry, RegistryQuery](daos.registryDAO, daos.auditLogDAO, daos.organizationDAO, validator)
  with UniqueKeySearch[Registry, RegistryQuery] {
  def orgId(d: Registry): Long = d.organizationId

  /** populate registry with system ids */
  override def hydrate(r: Registry): Future[Registry] =
    for { ids <- daos.systemDAO.runAction(systemQuery.filter(_.registryId === r.id).map(_.id).result) } yield r
      .copy(systems = Some(Left(ids)))

  // -----------------------------------------------------------
  //                  Auditing service methods
  // -----------------------------------------------------------
  override def createAudited(record: Registry, versionStamp: Long, ctx: RequestContext): Future[Registry] = {
    for {
      r <- registryDAO.create(record.copy(versionStamp = Some(versionStamp)))
      _ <- record.systems match {
        case Some(Left(ids)) => daos.systemDAO.setRegistryIds(r.id, _.id inSet ids)
        case _               => Future.successful(0)
      }
    } yield r

  }

  override def updateAudited(
    record: Registry,
    versionStamp: Long,
    previous: Registry,
    ctx: RequestContext
  ): Future[Option[Registry]] =
    for {
      r <- daos.registryDAO.update(record.copy(versionStamp = Some(versionStamp)))
      _ <- record.systems match {
        case Some(Left(ids)) =>
          daos.systemDAO.setRegistryIds(record.id, _.id inSet ids)
          daos.systemDAO.unsetRegistryIds(s => !(s.id inSet ids) && s.registryId === record.id)

        case _ => Future.successful(0)
      }
    } yield r

  /** Since we are allowing systems to exist without a registry, on deletion set the registry id of any
    * systems that refer to it to nulls.
    */

  override def deleteAudited(id: Long, versionStamp: Long, previous: Registry, ctx: RequestContext): Future[Int] =
    for {
      i <- super.deleteAudited(id, versionStamp, previous, ctx)
      _ <- daos.systemDAO.unsetRegistryIds(_.registryId === id)
    } yield i

  def findByUniqueKeyQuery(organizationId: Long, key: String): RegistryQuery => Rep[Boolean] = { q =>
    q.fidesKey === key && q.organizationId === organizationId
  }
}
