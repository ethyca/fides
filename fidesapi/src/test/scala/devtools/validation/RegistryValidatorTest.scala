package devtools.validation

import devtools.App
import devtools.Generators.RegistryGen
import devtools.domain.Registry
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class RegistryValidatorTest
  extends ValidatorTestBase[Registry, Long](RegistryGen, App.registryDAO, App.registryValidator) {

  test("only accept valid organizationIds") {
    createValidationErrors(_.copy(organizationId = randomLong)) should containMatchString("given as the organizationId")
  }
  test("invalid registry fides key fails") {
    createValidationErrors(_.copy(fidesKey = "an.illegal.key")) should containMatchString(
      "'an.illegal.key' is not a valid identifier."
    )
  }

}
