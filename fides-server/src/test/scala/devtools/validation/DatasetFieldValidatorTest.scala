package devtools.validation
import devtools.App
import devtools.Generators.DatasetFieldGen
import devtools.domain.DatasetField
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DatasetFieldValidatorTest
  extends ValidatorTestBase[DatasetField, Long](DatasetFieldGen, App.datasetFieldDAO, App.datasetFieldValidator) {

  test("create requires belonging to a table with a valid organization") {
    createValidationErrors(_.copy(datasetTableId = randomLong)) should containMatchString("no parent")
  }

  test("create requires categories to exist") {
    createValidationErrors(
      _.copy(datasetTableId = 1, dataCategories = Some(Set("not_a_valid_category")))
    ) should containMatchString("data category does not exist")
  }

  test("create requires qualifier to exist") {
    createValidationErrors(
      _.copy(datasetTableId = 1, dataQualifier = Some("not_a_valid_qualifier"))
    ) should containMatchString(" data qualifier does not exist")
  }

}
