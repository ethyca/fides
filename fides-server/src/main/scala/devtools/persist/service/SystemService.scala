package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.controller.RequestContext
import devtools.domain.SystemObject
import devtools.persist.dao.DAOs
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.SystemValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class SystemService(
  daos: DAOs,
  val policyService: PolicyService,
  val validator: SystemValidator
)(implicit
  val ec: ExecutionContext
) extends AuditingService[SystemObject](daos.systemDAO, daos.auditLogDAO, daos.organizationDAO, validator)
  with LazyLogging with UniqueKeySearch[SystemObject] {

  /** retrieve an org id from the base type */
  override def orgId(t: SystemObject): Long = t.organizationId

  /** actual create action that runs post validations, audit changes, and any other type-specific actions. */
  override def createAudited(record: SystemObject, versionStamp: Long, ctx: RequestContext): Future[SystemObject] =
    dao.create(record.copy(versionStamp = Some(versionStamp)))

  /** actual update action that runs post validations, audit changes, and any other type-specific actions. */
  override def updateAudited(
    record: SystemObject,
    versionStamp: Long,
    previous: SystemObject,
    ctx: RequestContext
  ): Future[Option[SystemObject]] =
    //TODO policy rating
    for {
      updated <- dao.update(record.copy(versionStamp = Some(versionStamp)))
      _ = record.registryId.map(daos.registryDAO.setVersion(_, versionStamp))
    } yield updated

  /** actual delete action that runs post validations, audit changes, and any other type-specific actions. */
  override def deleteAudited(id: Long, versionStamp: Long, previous: SystemObject, ctx: RequestContext): Future[Int] =
    for {
      deleted <- dao.delete(id)
      _ = previous.registryId.map(daos.registryDAO.setVersion(_, versionStamp))
    } yield deleted

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[SystemObject]] =
    daos.systemDAO.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
