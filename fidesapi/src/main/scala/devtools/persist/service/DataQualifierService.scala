package devtools.persist.service

import devtools.domain.DataQualifier
import devtools.persist.dao.{AuditLogDAO, DataQualifierDAO, OrganizationDAO}
import devtools.persist.db.Tables.DataQualifierQuery
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataQualifierValidator
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.ExecutionContext

class DataQualifierService(
  override val dao: DataQualifierDAO,
  AuditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataQualifierValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataQualifier, DataQualifierQuery](dao, AuditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataQualifier, DataQualifierQuery] {
  def orgId(d: DataQualifier): Long = d.organizationId

  def findByUniqueKeyQuery(organizationId: Long, key: String): DataQualifierQuery => Rep[Boolean] = { q =>
    q.fidesKey === key && q.organizationId === organizationId
  }
}
