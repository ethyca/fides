package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DataUse
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataUseValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DataUse, Long] with ValidateByOrganization {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(du: DataUse, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(du, new MessageCollector)
      .flatMap(requireOrganizationIdExists(du.organizationId, _))
      .flatMap(_.asFuture())

  /** Require that organization id exists,
    * parent id exists,
    * any altered fides keys are not in use
    */
  override def validateForUpdate(du: DataUse, existing: DataUse, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(du, new MessageCollector)
      .flatMap(requireOrganizationIdExists(du.organizationId, _))
      .flatMap { e =>
        if (existing.fidesKey != du.fidesKey) {
          fidesKeyInUseInSystem(existing, e).flatMap(fidesKeyInUseInPolicyRule(existing, _))
        } else {
          Future.successful(e)
        }
      }
      .flatMap(_.asFuture())

  override def validateForDelete(pk: Long, existing: DataUse, ctx: RequestContext): Future[Unit] =
    fidesKeyInUseInSystem(existing, new MessageCollector)
      .flatMap(fidesKeyInUseInSystem(existing, _))
      .flatMap(fidesKeyInUseInPolicyRule(existing, _))
      .flatMap(hasChildren(pk, _))
      .flatMap(_.asFuture())

  def hasChildren(id: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.dataUseDAO.runAction(
      daos.dataUseDAO.query.filter(d => d.parentId === id).map(_.id).result
    ) map { ids =>
      if (ids.nonEmpty) {
        errors.addError(s"The selected node cannot be deleted because it has has child nodes.")
      }
      errors
    }

  /** Require that the parent key exists or is 0 (root) */
  def requireParentIdExists(du: DataUse, errors: MessageCollector): Future[MessageCollector] =
    du.parentId match {
      case Some(pid) =>
        daos.dataUseDAO.exists(d => (d.parentId === pid) && (d.organizationId === du.organizationId)).map { exists =>
          if (!exists) {
            errors.addError(s"The value '${du.parentId.getOrElse("")}' given as the parentId does not exist.")
          }
          errors
        }
      case _ => Future.successful(errors)
    }

  def fidesKeyInUseInSystem(dataUse: DataUse, errors: MessageCollector): Future[MessageCollector] =
    daos.systemDAO
      .findSystemsWithJsonMember(dataUse.organizationId, dataUse.fidesKey, "dataUse")
      .map { systemIds =>
        if (systemIds.nonEmpty) {
          errors.addError(s"The fides key ${dataUse.fidesKey} is in use in systems ${systemIds.mkString(",")}")
        }
        errors
      }

  def fidesKeyInUseInPolicyRule(dataUse: DataUse, errors: MessageCollector): Future[MessageCollector] =
    daos.policyRuleDAO.findPolicyRuleWithDataUse(dataUse.organizationId, dataUse.fidesKey).map { ruleIds =>
      if (ruleIds.nonEmpty) {
        errors.addError(s"The fides key ${dataUse.fidesKey} is in use in policy rules ${ruleIds.mkString(",")}")
      }
      errors
    }

}
