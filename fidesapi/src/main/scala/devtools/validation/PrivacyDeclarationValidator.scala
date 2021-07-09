package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.PrivacyDeclaration
import devtools.persist.dao.DAOs

import scala.concurrent.{ExecutionContext, Future}

class PrivacyDeclarationValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[PrivacyDeclaration, Long] with ValidateByTaxonomy {

  def validateForCreate(t: PrivacyDeclaration, ctx: RequestContext): Future[Unit] = {
    //TODO
    Future.successful(())

  }

}
