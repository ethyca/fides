package devtools.validation

import devtools.Generators.PolicyRuleGen
import devtools.domain.enums.PolicyValueGrouping
import devtools.domain.enums.RuleInclusion.ALL
import devtools.domain.policy.{Policy, PolicyRule}
import devtools.util.waitFor
import devtools.{App, Generators}
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class PolicyRuleValidatorTest
  extends ValidatorTestBase[PolicyRule, Long](PolicyRuleGen, App.policyRuleDAO, App.policyRuleValidator) {

  /** Create a new empty policy for id existence check */
  var policyId: Long = 0

  override def beforeAll(): Unit = {
    policyId = waitFor(
      App.policyDAO.create(Policy(0, 1, Generators.fidesKey, Some(0L), None, None, None, None, None))
    ).id
  }

  override def afterAll(): Unit = App.policyDAO.delete(policyId)

  test("only accept valid data categories") {
    createValidationErrors(
      _.copy(dataCategories = PolicyValueGrouping(ALL, Set("IamNotALegalDataCategory")))
    ) should containMatchString("IamNotALegalDataCategory")
  }

  test("Only accept valid qualifiers") {
    createValidationErrors(_.copy(dataQualifier = Some("IamNotALegalDataQualifier"))) should containMatchString(
      "IamNotALegalDataQualifier"
    )
  }

  test("Only accept valid data use") {
    createValidationErrors(
      _.copy(dataUses = PolicyValueGrouping(ALL, Set("IamNotALegalDataUse", "NeitherAmI")))
    ) should containMatchString("NeitherAmI")
  }

}
