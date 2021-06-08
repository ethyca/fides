package devtools.persist.service

import devtools.domain.DataCategory
import devtools.persist.dao.{AuditLogDAO, DataCategoryDAO, OrganizationDAO}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataCategoryValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataCategoryService(
  override val dao: DataCategoryDAO,
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataCategoryValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataCategory](dao, auditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataCategory] {

  def orgId(d: DataCategory): Long = d.organizationId

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DataCategory]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)
}
