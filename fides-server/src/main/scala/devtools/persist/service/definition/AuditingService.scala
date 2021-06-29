package devtools.persist.service.definition

import devtools.controller.RequestContext
import devtools.domain.AuditLog
import devtools.domain.definition.{IdType, OrganizationId}
import devtools.domain.enums.AuditAction
import devtools.persist.dao.definition.{ByOrganizationDAO, DAO}
import devtools.persist.dao.{AuditLogDAO, OrganizationDAO}
import devtools.persist.db.{BaseAutoIncTable, OrganizationIdTable}
import devtools.util.JsonSupport
import devtools.util.JsonSupport.difference
import devtools.validation.Validator
import org.json4s.JValue

import scala.concurrent.{ExecutionContext, Future}

/** Extension of a service by organization that creates audit log entries on CREATE/UPDATE/DELETE operations. */
abstract class AuditingService[E <: IdType[E, Long] with OrganizationId](
  dao: DAO[E, Long, _ <: BaseAutoIncTable[E] with OrganizationIdTable[E]] with ByOrganizationDAO[E, _],
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  validator: Validator[E, Long]
)(implicit ec: ExecutionContext, m: Manifest[E])
  extends ByOrganizationService[E](dao, validator) {

  /** retrieve an org id from the base type */
  def orgId(t: E): Long

  //auditing support objects
  def createValue(t: E, orgId: Long, versionStamp: Option[Long], userId: Long): AuditLog =
    AuditLog(
      0,
      t.id,
      orgId,
      versionStamp,
      userId,
      AuditAction.CREATE,
      t.getClass.getSimpleName,
      None,
      Some(JsonSupport.toAST[E](t)),
      None,
      None
    )

  def updateValue(t: E, previous: E, orgId: Long, versionStamp: Option[Long], userId: Long): AuditLog = {
    val from: JValue = JsonSupport.toAST[E](previous)
    val to: JValue   = JsonSupport.toAST[E](t)
    val diff         = difference(from, to)
    AuditLog(
      0,
      t.id,
      orgId,
      versionStamp,
      userId,
      AuditAction.UPDATE,
      t.getClass.getSimpleName,
      Some(from),
      Some(to),
      Some(diff),
      None
    )
  }

  def deleteValue(
    id: Long,
    previous: E,
    orgId: Long,
    versionStamp: Option[Long],
    userId: Long,
    className: String
  ): AuditLog =
    AuditLog(
      0,
      id,
      orgId,
      versionStamp,
      userId,
      AuditAction.DELETE,
      className,
      Some(JsonSupport.toAST[E](previous)),
      None,
      None,
      None
    )

  /** actual create action that runs post validations, audit changes, and any other type-specific actions. */
  def createAudited(record: E, versionStamp: Long, ctx: RequestContext): Future[E] = dao.create(record)

  /** actual update action that runs post validations, audit changes, and any other type-specific actions. */
  def updateAudited(record: E, versionStamp: Long, previous: E, ctx: RequestContext): Future[Option[E]] =
    dao.update(record)

  /** actual delete action that runs post validations, audit changes, and any other type-specific actions. */
  def deleteAudited(id: Long, versionStamp: Long, previous: E, ctx: RequestContext): Future[Int] = dao.delete(id)

  override def createValidated(record: E, ctx: RequestContext): Future[E] =
    for {
      versionStamp <- organizationDAO.getAndIncrementVersion(orgId(record))
      created      <- createAudited(record, versionStamp, ctx)
      _            <- auditLogDAO.create(createValue(created, orgId(created), Some(versionStamp), ctx.user.id))
    } yield created

  override def updateValidated(record: E, previous: E, ctx: RequestContext): Future[Option[E]] =
    for {
      versionStamp <- organizationDAO.getAndIncrementVersion(orgId(record))
      updated      <- updateAudited(record, versionStamp, previous, ctx)
      _            <- auditLogDAO.create(updateValue(updated.get, previous, orgId(updated.get), Some(versionStamp), ctx.user.id))
    } yield updated

  override def deleteValidated(id: Long, previous: E, ctx: RequestContext): Future[Int] =
    for {
      versionStamp <- organizationDAO.getAndIncrementVersion(orgId(previous))
      i            <- deleteAudited(id, versionStamp, previous, ctx)
      _ <- auditLogDAO.create(
        deleteValue(id, previous, orgId(previous), Some(versionStamp), ctx.user.id, m.runtimeClass.getSimpleName)
      )

    } yield i

}
