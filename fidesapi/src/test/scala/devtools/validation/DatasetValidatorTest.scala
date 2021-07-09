package devtools.validation

import devtools.App
import devtools.Generators.DatasetGen
import devtools.domain.Dataset
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DatasetValidatorTest extends ValidatorTestBase[Dataset, Long](DatasetGen, App.datasetDAO, App.datasetValidator) {

  test("create requires organization to exist") {
    createValidationErrors(_.copy(organizationId = randomLong)) should containMatchString("organization")
  }

}
