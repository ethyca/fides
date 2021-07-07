package devtools.persist.service

import devtools.domain.PrivacyDeclaration
import devtools.persist.dao.DAOs
import devtools.persist.service.definition.Service
import devtools.validation.PrivacyDeclarationValidator

import scala.concurrent.ExecutionContext

class PrivacyDeclarationService(val daos: DAOs, val validator: PrivacyDeclarationValidator)(implicit
  val context: ExecutionContext
) extends Service[PrivacyDeclaration, Long](daos.privacyDeclarationDAO, validator) {}
