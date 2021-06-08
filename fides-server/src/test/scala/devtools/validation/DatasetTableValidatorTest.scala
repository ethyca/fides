package devtools.validation

import devtools.App
import devtools.Generators.DatasetTableGen
import devtools.domain.DatasetTable
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DatasetTableValidatorTest
  extends ValidatorTestBase[DatasetTable, Long](DatasetTableGen, App.datasetTableDAO, App.datasetTableValidator) {

  test("create requires belonging to a table with a valid organization") {
    createValidationErrors(_.copy(datasetId = randomLong)) should containMatchString("dataset")
  }
}
