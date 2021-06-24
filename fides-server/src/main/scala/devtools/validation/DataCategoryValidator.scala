package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DataCategory
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DataCategoryValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DataCategory, Long] with ValidateByOrganization {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(dc: DataCategory, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(dc, new MessageCollector)
      .flatMap(requireOrganizationIdExists(dc.organizationId, _))
      .flatMap(_.asFuture())

  /** Require that organization id exists,
    * parent id exists,
    * any altered fides keys are not in use
    */
  override def validateForUpdate(dc: DataCategory, existing: DataCategory, ctx: RequestContext): Future[Unit] =
    requireParentIdExists(dc, new MessageCollector)
      .flatMap(requireOrganizationIdExists(dc.organizationId, _))
      .flatMap { e =>
        if (existing.fidesKey != dc.fidesKey) {
          fidesKeyInUseInSystem(existing, e).flatMap(fidesKeyInUseInPolicyRule(existing, _))
        } else {
          Future.successful(e)
        }
      }
      .flatMap(_.asFuture())

  /** Deletion validations for taxonomy types have to ensure that those values are not referenced
    * by any existing systems or policy rules. */
  override def validateForDelete(pk: Long, existing: DataCategory, ctx: RequestContext): Future[Unit] =
    fidesKeyInUseInSystem(existing, new MessageCollector)
      .flatMap(fidesKeyInUseInSystem(existing, _))
      .flatMap(fidesKeyInUseInPolicyRule(existing, _))
      .flatMap(hasChildren(pk, _))
      .flatMap(_.asFuture())

  /**Add to errors (fail) if this category has child values. since this would create orphan records. */
  def hasChildren(id: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.dataCategoryDAO.runAction(
      daos.dataCategoryDAO.query.filter(d => d.parentId === id && d.id =!= id).map(_.id).result
    ) map { ids =>
      if (ids.nonEmpty) {
        errors.addError(s"The selected node cannot be deleted because it has has child nodes.")
      }
      errors
    }

  /** Require that the parent key exists or that this value is a root value */
  def requireParentIdExists(dc: DataCategory, errors: MessageCollector): Future[MessageCollector] =
    dc.parentId match {
      case Some(pid) =>
        daos.dataCategoryDAO.exists(d => (d.parentId === pid) && (d.organizationId === dc.organizationId)).map {
          exists =>
            if (!exists) {
              errors.addError(s"The value '${dc.parentId.getOrElse("")}' given as the parentId does not exist.")
            }
            errors
        }
      case _ => Future.successful(errors)
    }

  /** Add to errors if the data category key is found in any existing system in this organization. */
  def fidesKeyInUseInSystem(dc: DataCategory, errors: MessageCollector): Future[MessageCollector] =
    daos.systemDAO
      .findSystemsWithJsonMember(dc.organizationId, dc.fidesKey, "dataCategories")
      .map { systemIds =>
        if (systemIds.nonEmpty) {
          errors.addError(s"The fides key ${dc.fidesKey} is in use in systems ${systemIds.mkString(",")}")
        }
        errors
      }
  /** Add to errors if the data category key is found in any existing policy rule. */
  def fidesKeyInUseInPolicyRule(dc: DataCategory, errors: MessageCollector): Future[MessageCollector] =
    daos.policyRuleDAO.findPolicyRuleWithDataCategory(dc.organizationId, dc.fidesKey).map { ruleIds =>
      if (ruleIds.nonEmpty) {
        errors.addError(s"The fides key ${dc.fidesKey} is in use in policy rules ${ruleIds.mkString(",")}")
      }
      errors
    }

}
