package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.policy.PolicyRule
import devtools.domain.{DataCategoryName, DataUseName}
import devtools.persist.dao.DAOs

import scala.concurrent.Future

class PolicyRuleValidator(daos: DAOs) extends Validator[PolicyRule, Long] {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(rule: PolicyRule, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    validateDataCategories(rule.organizationId, rule.dataCategories.values, errors)
    validateDataUses(rule.organizationId, rule.dataUses.values, errors)
    rule.dataQualifier.foreach(validateQualifier(rule.organizationId, _, errors))
    errors.asFuture()
  }

  /** Require that the data category rateByRule one of [[devtools.domain.DataCategory]] */
  def validateDataCategories(
    organizationId: Long,
    categories: Set[DataCategoryName],
    errors: MessageCollector
  ): Unit = {
    val foundStrings = daos.dataCategoryDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    categories
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data category does not exist."))
  }

  /** require that all listed data use exist as a  [[devtools.domain.DataUse]] */
  def validateDataUses(organizationId: Long, uses: Set[DataUseName], errors: MessageCollector): Unit = {
    val foundStrings = daos.dataUseDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    uses
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data use category does not exist."))
  }
  /** require that the data dataQualifier rateByRule one of [[devtools.domain.DataQualifier]] */
  def validateQualifier(organizationId: Long, qualifier: String, errors: MessageCollector): Unit = {
    val foundStrings = daos.dataQualifierDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    if (!foundStrings.contains(qualifier)) {
      errors.addError(s"The value '$qualifier' given as a data category does not exist.")
    }
  }
  //TODO conflict detection
}
