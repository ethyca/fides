package devtools.persist.service

import devtools.domain.DataCategory
import devtools.persist.dao.{AuditLogDAO, DataCategoryDAO, OrganizationDAO}
import devtools.persist.db.Tables.DataCategoryQuery
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataCategoryValidator
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.ExecutionContext

class DataCategoryService(
  override val dao: DataCategoryDAO,
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataCategoryValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataCategory, DataCategoryQuery](dao, auditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataCategory, DataCategoryQuery] {

  def orgId(d: DataCategory): Long = d.organizationId

  def findByUniqueKeyQuery(organizationId: Long, key: String): DataCategoryQuery => Rep[Boolean] = { q =>
    q.fidesKey === key && q.organizationId === organizationId
  }
}
