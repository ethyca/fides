package devtools.persist.service

import devtools.domain.AuditLog
import devtools.persist.dao.AuditLogDAO
import devtools.persist.db.Tables.AuditLogQuery
import devtools.persist.service.definition.ByOrganizationService
import devtools.validation.Validator

import scala.concurrent.ExecutionContext

class AuditLogService(dao: AuditLogDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[AuditLog, AuditLogQuery](dao, Validator.noOp[AuditLog, Long])(context) {}
