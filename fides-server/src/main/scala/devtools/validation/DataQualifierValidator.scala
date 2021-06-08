package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DataQualifier
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataQualifierValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DataQualifier, Long] with ValidateByOrganization {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(dq: DataQualifier, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(dq, new MessageCollector)
      .flatMap(requireOrganizationIdExists(dq.organizationId, _))
      .flatMap(_.asFuture())
  /** Require that organization id exists,
    * parent id exists,
    * any altered fides keys are not in use
    */
  override def validateForUpdate(dq: DataQualifier, existing: DataQualifier, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(dq, new MessageCollector)
      .flatMap(requireOrganizationIdExists(dq.organizationId, _))
      .flatMap { e =>
        if (existing.fidesKey != dq.fidesKey) {
          fidesKeyInUseInSystem(existing, e).flatMap(fidesKeyInUseInPolicyRule(existing, _))
        } else {
          Future.successful(e)
        }
      }
      .flatMap(_.asFuture())

  override def validateForDelete(pk: Long, existing: DataQualifier, ctx: RequestContext): Future[Unit] =
    fidesKeyInUseInSystem(existing, new MessageCollector)
      .flatMap(fidesKeyInUseInSystem(existing, _))
      .flatMap(fidesKeyInUseInPolicyRule(existing, _))
      .flatMap(hasChildren(pk, _))
      .flatMap(_.asFuture())

  def hasChildren(id: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.dataQualifierDAO.runAction(
      daos.dataQualifierDAO.query.filter(d => d.parentId === id).map(_.id).result
    ) map { ids =>
      if (ids.nonEmpty) {
        errors.addError(s"The selected node cannot be deleted because it has has child nodes.")
      }
      errors
    }

  /** Require that the parent key exists or is 0 (root) */
  def requireParentIdExists(dq: DataQualifier, errors: MessageCollector): Future[MessageCollector] =
    dq.parentId match {

      case Some(pid) =>
        daos.dataQualifierDAO.exists(d => (d.parentId === pid) && (d.organizationId === dq.organizationId)).map {
          exists =>
            if (!exists) {
              errors.addError(s"The value '${dq.parentId.getOrElse("")}' given as the parentId does not exist.")
            }
            errors
        }

      case _ => Future.successful(errors)
    }

  def fidesKeyInUseInSystem(dq: DataQualifier, errors: MessageCollector): Future[MessageCollector] =
    daos.systemDAO
      .findSystemsWithJsonMember(dq.organizationId, dq.fidesKey, "dataQualifier")
      .map { systemIds =>
        if (systemIds.nonEmpty) {
          errors.addError(s"The fides key ${dq.fidesKey} is in use in systems ${systemIds.mkString(",")}")
        }
        errors
      }

  def fidesKeyInUseInPolicyRule(dq: DataQualifier, errors: MessageCollector): Future[MessageCollector] =
    daos.policyRuleDAO.findPolicyRuleWithDataQualifer(dq.organizationId, dq.fidesKey).map { ruleIds =>
      if (ruleIds.nonEmpty) {
        errors.addError(s"The fides key ${dq.fidesKey} is in use in policy rules ${ruleIds.mkString(",")}")
      }
      errors
    }

}
