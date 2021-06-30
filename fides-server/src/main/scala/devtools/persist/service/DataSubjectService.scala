package devtools.persist.service

import devtools.domain.DataSubject
import devtools.persist.dao.{AuditLogDAO, DataSubjectDAO, OrganizationDAO}
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DataSubjectValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataSubjectService(
  override val dao: DataSubjectDAO,
  auditLogDAO: AuditLogDAO,
  organizationDAO: OrganizationDAO,
  val validator: DataSubjectValidator
)(implicit val ctx: ExecutionContext)
  extends AuditingService[DataSubject](dao, auditLogDAO, organizationDAO, validator) with UniqueKeySearch[DataSubject] {

  def orgId(d: DataSubject): Long = d.organizationId

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DataSubject]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
