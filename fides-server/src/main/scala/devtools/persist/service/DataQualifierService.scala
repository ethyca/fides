package devtools.persist.service

import devtools.domain.DataQualifier
import devtools.persist.dao.{AuditLogDAO, DataQualifierDAO, OrganizationDAO}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataQualifierValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataQualifierService(
  override val dao: DataQualifierDAO,
  AuditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataQualifierValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataQualifier](dao, AuditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataQualifier] {
  def orgId(d: DataQualifier): Long = d.organizationId

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DataQualifier]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
