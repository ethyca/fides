package devtools.validation

import devtools.App
import devtools.Generators.{PolicyGen, fidesKey}
import devtools.domain.Organization
import devtools.domain.policy.Policy
import devtools.util.waitFor
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class PolicyValidatorTest extends ValidatorTestBase[Policy, Long](PolicyGen, App.policyDAO, App.policyValidator) {

  /** Create a new empty policy for id existence check */
  var organizationId: Long = 0

  override def beforeAll(): Unit = {
    organizationId = waitFor(
      App.organizationDAO.create(Organization(0, fidesKey, None, None, None, None, None))
    ).id
  }

  override def afterAll(): Unit = App.organizationDAO.delete(organizationId)

  test("only accept valid organizationIds") {
    createValidationErrors(_.copy(organizationId = randomLong)) should containMatchString("given as the organizationId")
  }
  test("invalid policy fides key fails") {
    createValidationErrors(_.copy(fidesKey = "an.illegal.key")) should containMatchString(
      "'an.illegal.key' is not a valid identifier."
    )
  }

}
