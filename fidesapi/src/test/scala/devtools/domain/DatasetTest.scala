package devtools.domain

import com.typesafe.scalalogging.LazyLogging
import devtools.TestUtils
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DatasetTest extends AnyFunSuite with LazyLogging with TestUtils {

  test("test get privacy map") {
    val d = datasetOf(Some("qualifierA"), Some(Set("cat1", "cat2")))
    d.qualifierCategoriesMap() shouldBe Map("qualifierA" -> Set("cat1", "cat2"))
  }

  test("test get privacy field map") {
    val d = datasetOf(None, None, datasetFieldOf("a", "qualifierA", Set("cat1", "cat2")))
    d.getField("a").map(d.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))
    //field b doesn't exist
    d.getField("b").map(d.qualifierCategoriesMapForField) shouldBe None
    //when the field values aren't set the general values are used
    val d2 = datasetOf(
      Some("qualifierA"),
      Some(Set("cat1", "cat2")),
      datasetFieldOf("a")
        .copy(dataQualifier = None, dataCategories = None)
    )
    d2.getField("a").map(d2.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))
    //if only 1 field value is provided,  use the general values
    val d3 = datasetOf(
      Some("qualifierA"),
      Some(Set("cat1", "cat2")),
      datasetFieldOf("a", "qualifierB", Set())
        .copy(dataCategories = None)
    )
    d3.getField("a").map(d3.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))
    val d4 = datasetOf(
      Some("qualifierA"),
      Some(Set("cat1", "cat2")),
      datasetFieldOf("a", "x", Set("cat1", "cat2")).copy(dataQualifier = None)
    )
    d4.getField("a").map(d4.qualifierCategoriesMapForField) shouldBe Some(Map("qualifierA" -> Set("cat1", "cat2")))

  }

  test("test basename") {
    Dataset.baseName(".") shouldBe None
    Dataset.baseName("") shouldBe None
    Dataset.baseName("a") shouldBe Some("a")
    Dataset.baseName("a.b") shouldBe Some("a")
    Dataset.baseName("a.b.c") shouldBe Some("a")
  }
}
