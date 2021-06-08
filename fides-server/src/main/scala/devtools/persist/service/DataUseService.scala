package devtools.persist.service

import devtools.domain.DataUse
import devtools.persist.dao.{AuditLogDAO, DataUseDAO, OrganizationDAO}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataUseValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataUseService(
  override val dao: DataUseDAO,
  AuditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataUseValidator
)(implicit
  val ctx: ExecutionContext
) extends AuditingService[DataUse](dao, AuditLogDAO, organizationDAO, validator) with UniqueKeySearch[DataUse] {

  def orgId(d: DataUse): Long = d.organizationId

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DataUse]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
