package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DataSubject
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataSubjectValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DataSubject, Long] with ValidateByOrganization {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(sc: DataSubject, ctx: RequestContext): Future[Unit] = {
    requireParentIdExists(sc, new MessageCollector)
      .flatMap(requireOrganizationIdExists(sc.organizationId, _))
      .flatMap(_.asFuture())
  }

  /** Require that organization id exists,
    * parent id exists,
    * any altered fides keys are not in use
    */
  override def validateForUpdate(
    sc: DataSubject,
    existing: DataSubject,
    ctx: RequestContext
  ): Future[Unit] =
    requireParentIdExists(sc, new MessageCollector)
      .flatMap(requireOrganizationIdExists(sc.organizationId, _))
      .flatMap { e =>
        if (existing.fidesKey != sc.fidesKey) {
          fidesKeyInUseInSystem(existing, e).flatMap(fidesKeyInUseInPolicyRule(existing, _))
        } else {
          Future.successful(e)
        }
      }
      .flatMap(_.asFuture())

  /** Deletion validations for taxonomy types have to ensure that those values are not referenced
    * by any existing systems or policy rules.
    */
  override def validateForDelete(pk: Long, existing: DataSubject, ctx: RequestContext): Future[Unit] =
    fidesKeyInUseInSystem(existing, new MessageCollector)
      .flatMap(fidesKeyInUseInSystem(existing, _))
      .flatMap(fidesKeyInUseInPolicyRule(existing, _))
      .flatMap(hasChildren(pk, _))
      .flatMap(_.asFuture())

  /** Add to errors (fail) if this subject category has child values. since this would create orphan records. */
  def hasChildren(id: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.dataSubjectDAO.runAction(
      daos.dataSubjectDAO.query.filter(d => d.parentId === id).map(_.id).result
    ) map { ids =>
      if (ids.nonEmpty) {
        errors.addError(s"The selected node cannot be deleted because it has has child nodes.")
      }
      errors
    }

  /** Require that the parent key exists or that this value is a root value */
  def requireParentIdExists(dq: DataSubject, errors: MessageCollector): Future[MessageCollector] =
    dq.parentId match {
      case Some(pid) =>
        daos.dataSubjectDAO
          .exists(d => (d.parentId === pid) && (d.organizationId === dq.organizationId))
          .map { exists =>
            if (!exists) {
              errors.addError(s"The value '${dq.parentId.getOrElse("")}' given as the parentId does not exist.")
            }
            errors
          }

      case _ => Future.successful(errors)
    }

  /** Add to errors if the data subject category key is found in any existing system in this organization. */
  def fidesKeyInUseInSystem(dataUse: DataSubject, errors: MessageCollector): Future[MessageCollector] =
    daos.systemDAO
      .findSystemsWithJsonMember(dataUse.organizationId, dataUse.fidesKey, "dataSubjectCategories")
      .map { systemIds =>
        if (systemIds.nonEmpty) {
          errors.addError(s"The fides key ${dataUse.fidesKey} is in use in systems ${systemIds.mkString(",")}")
        }
        errors
      }

  /** Add to errors if the data subject category key is found in any existing policy rule. */
  def fidesKeyInUseInPolicyRule(dataUse: DataSubject, errors: MessageCollector): Future[MessageCollector] =
    daos.policyRuleDAO.findPolicyRuleWithSubjectCategory(dataUse.organizationId, dataUse.fidesKey).map { ruleIds =>
      if (ruleIds.nonEmpty) {
        errors.addError(s"The fides key ${dataUse.fidesKey} is in use in policy rules ${ruleIds.mkString(",")}")
      }
      errors
    }

}
