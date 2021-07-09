package devtools.persist.service

import devtools.domain.DataSubject
import devtools.persist.dao.{AuditLogDAO, DataSubjectDAO, OrganizationDAO}
import devtools.persist.db.Tables.DataSubjectQuery
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataSubjectValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext

class DataSubjectService(
  override val dao: DataSubjectDAO,
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataSubjectValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataSubject, DataSubjectQuery](dao, auditLogDAO, organizationDAO, validator)
  with UniqueKeySearch[DataSubject, DataSubjectQuery] {

  def orgId(d: DataSubject): Long = d.organizationId

  def findByUniqueKeyQuery(organizationId: Long, key: String): DataSubjectQuery => Rep[Boolean] = { t =>
    t.fidesKey === key && t.organizationId === organizationId
  }

}
