package devtools.persist.service

import devtools.domain.DataSubjectCategory
import devtools.persist.dao.{AuditLogDAO, DataSubjectCategoryDAO, OrganizationDAO}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataSubjectCategoryValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataSubjectCategoryService(
  override val dao: DataSubjectCategoryDAO,
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataSubjectCategoryValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataSubjectCategory](dao, auditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataSubjectCategory] {

  def orgId(d: DataSubjectCategory): Long = d.organizationId

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DataSubjectCategory]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
