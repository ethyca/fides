package devtools.persist.service

import devtools.domain.DataUse
import devtools.persist.dao.{AuditLogDAO, DataUseDAO, OrganizationDAO}
import devtools.persist.db.Tables.DataUseQuery
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataUseValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext

class DataUseService(
  override val dao: DataUseDAO,
  AuditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataUseValidator
)(implicit
  val ctx: ExecutionContext
) extends AuditingService[DataUse, DataUseQuery](dao, AuditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataUse, DataUseQuery] {

  def orgId(d: DataUse): Long = d.organizationId

  def findByUniqueKeyQuery(organizationId: Long, key: String): DataUseQuery => Rep[Boolean] = { q =>
    q.fidesKey === key && q.organizationId === organizationId
  }

}
