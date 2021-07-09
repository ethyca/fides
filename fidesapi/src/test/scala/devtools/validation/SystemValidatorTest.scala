package devtools.validation

import devtools.App
import devtools.Generators.{DeclarationGen, SystemObjectGen, blankSystem, fidesKey}
import devtools.domain.SystemObject
import devtools.util.waitFor
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class SystemValidatorTest
  extends ValidatorTestBase[SystemObject, Long](SystemObjectGen, App.systemDAO, App.systemValidator) {
  val name1: String = fidesKey

  override def beforeAll(): Unit = {
    createdIds.add(waitFor(dao.create(blankSystem.copy(fidesKey = name1))).id)
    createdIds.add(waitFor(dao.create(blankSystem)).id)
    createdIds.add(waitFor(dao.create(blankSystem.copy(organizationId = 2))).id)
  }

  test("Only data subject use categories that exist in db are accepted") {
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(dataSubjects = Set("not a valid data subject"))))
      )
    ) should containMatchString("data subject")
  }

  test("Only valid registry ids") {
    createValidationErrors(blankSystem.copy(registryId = Some(randomLong))) should containMatchString("registry id ")
    createValidationErrors(blankSystem.copy(registryId = None)) shouldNot containMatchString("registry id ")
  }

  test("Only data use categories that exist in db are accepted") {
    createValidationErrors(
      blankSystem
        .copy(
          fidesKey = name1,
          privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(dataUse = "not_a_valid_data_use")))
        )
    ) should containMatchString("data use category")
  }

  test("Only data categories that exist in db are accepted") {
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations =
          Some(Seq(DeclarationGen.sample.get.copy(dataCategories = Set("not_a_valid_data_category"))))
      )
    ) should containMatchString("data category")
  }

  test("Only data qualifiers that exist in db are accepted") {
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(dataQualifier = "not_a_valid_qualifier")))
      )
    ) should containMatchString("data qualifier")
  }

  test("self reference invalid") {
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        systemDependencies = Set(name1)
      )
    ) should containMatchString(s"Invalid self reference")
  }

  test("test rawDatasets and dataset fields in declarations must exist") {
    // also test that they are searched for by their validated names
    // test with a mix of dataset, dataset field names
    // test that this works with a dataset name for a dataset record that exists
    // with no fields specified
    // fail("TODO")

    // this is search for by its sanitized name, "test-dataset_", which fails":
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(datasetReferences = Set("test_dataset "))))
      )
    ) should containMatchString("dataset")

    //using validated name works fine
    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(datasetReferences = Set("test dataset"))))
      )
    ) shouldNot containMatchString("dataset")

    createValidationErrors(
      blankSystem.copy(
        fidesKey = name1,
        privacyDeclarations =
          Some(Seq(DeclarationGen.sample.get.copy(datasetReferences = Set("test_dataset.not a field"))))
      )
    ) should containMatchString("not_a_field")

  }

}
