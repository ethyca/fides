package devtools.domain

import com.typesafe.scalalogging.LazyLogging
import devtools.TestUtils
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

/*
"aggregated_data": {
    "anonymized_data": {
      "unlinked_pseudonymized_data": {
        "pseudonymized_data": {
          "identified_data": {}



            "customer_content_data": [
    "credentials",
    "customer_contact_lists"]

      "cloud_service_provider_data": [
    "access_and_authentication_data",
    "operations_data"
  ],



 */

class DatasetTest extends AnyFunSuite with LazyLogging with TestUtils {

  test("test get privacy map") {
    val d = datasetOf(Some("qualifierA"), Some(Set("cat1", "cat2")))
    d.qualifierCategoriesMap() shouldBe Map("qualifierA" -> Set("cat1", "cat2"))

  }

  test("test get privacy field map") {
    val d = datasetOf(None, None, datasetFieldOf(Some("qualifierA"), Some(Set("cat1", "cat2"))))
    d.getField("a").map(d.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))
    //field b doesn't exist
    d.getField("b").map(d.qualifierCategoriesMapForField) shouldBe None
    //when the field values aren't set the general values are used
    val d2 = datasetOf(Some("qualifierA"), Some(Set("cat1", "cat2")), datasetFieldOf(None, None))
    d2.getField("a").map(d2.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))
    //if only 1 field value is provided,  use the general values
    val d3 = datasetOf(Some("qualifierA"), Some(Set("cat1", "cat2")), datasetFieldOf(Some("qualifierB"), None))
    d3.getField("a").map(d3.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))

    val d4 = datasetOf(Some("qualifierA"), Some(Set("cat1", "cat2")), datasetFieldOf(None, Some(Set("cat1", "cat2"))))
    d4.getField("a").map(d4.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))

  }
//  dataset: get privacy map
//  dataset field: get privacy map

  private def datasetOf(
    dataQualifier: Option[DataQualifierName],
    dataCategories: Option[Set[DataCategoryName]],
    fields: DatasetField*
  ) =
    Dataset(0L, 1L, "", None, None, None, None, dataCategories, dataQualifier, None, None, Some(fields), None, None)

  private def datasetFieldOf(
    dataQualifier: Option[DataQualifierName],
    dataCategories: Option[Set[DataCategoryName]]
  ): DatasetField =
    DatasetField(
      0L,
      0L,
      "a",
      None,
      None,
      dataCategories,
      dataQualifier,
      None,
      None
    )
}
