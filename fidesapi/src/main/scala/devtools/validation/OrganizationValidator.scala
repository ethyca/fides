package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.Organization

import scala.concurrent.{ExecutionContext, Future}

class OrganizationValidator()(implicit val executionContext: ExecutionContext) extends Validator[Organization, Long] {
  /** Perform any validations on the input object and collect any errors found.
    * Collect all errors found and return inside a ValidationException
    */
  override def validateForCreate(t: Organization, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector()
    validateFidesKey(t.fidesKey, errors)
    errors.asFuture()
  }
}
