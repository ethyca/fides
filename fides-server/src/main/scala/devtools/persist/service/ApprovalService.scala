package devtools.persist.service

import devtools.domain.Approval
import devtools.persist.dao.ApprovalDAO
import devtools.persist.service.definition.ByOrganizationService
import devtools.validation.Validator

import scala.concurrent.ExecutionContext

class ApprovalService(dao: ApprovalDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[Approval](dao, Validator.noOp[Approval, Long])(context) {}
