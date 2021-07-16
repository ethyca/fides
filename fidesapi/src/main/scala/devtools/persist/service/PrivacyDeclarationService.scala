package devtools.persist.service

import devtools.domain.PrivacyDeclaration
import devtools.persist.dao.DAOs
import devtools.persist.db.Tables.PrivacyDeclarationQuery
import devtools.persist.service.definition.Service
import devtools.validation.Validator

import scala.concurrent.ExecutionContext

class PrivacyDeclarationService(val daos: DAOs)(implicit
  val context: ExecutionContext
) extends Service[PrivacyDeclaration, Long, PrivacyDeclarationQuery](
    daos.privacyDeclarationDAO,
    Validator.noOp[PrivacyDeclaration, Long]
  ) {}
