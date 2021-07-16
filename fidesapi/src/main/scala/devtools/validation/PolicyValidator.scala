package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.policy.Policy
import devtools.persist.dao.DAOs

import scala.concurrent.{ExecutionContext, Future}

class PolicyValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[Policy, Long] with ValidateByOrganization {

  /** Validations:
    *
    * - require that referenced organization exists.
    */
  def validateForCreate(p: Policy, ctx: RequestContext): Future[Unit] =
    requireOrganizationIdExists(p.organizationId, new MessageCollector)
      .map(validateFidesKey(p.fidesKey, _))
      .flatMap(_.asFuture())

}
