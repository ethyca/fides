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

}
