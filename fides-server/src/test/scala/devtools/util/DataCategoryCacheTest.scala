package devtools.util

import devtools.Generators.{oneOf, smallSetOf}
import devtools.domain.DataCategory
import devtools.{App, TestUtils}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.{a, be, contain}
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.MySQLProfile.api._

import scala.collection.mutable.{Set => MSet}

class DataCategoryCacheTest extends AnyFunSuite with TestUtils {
  private val dao = App.dataCategoryDAO

  test("test cache root population") {
    //should be none but populates the cache
    dao.cacheGet(1, 0) shouldEqual None
    val roots: Seq[Int] =
      waitFor(dao.db.run(sql"""SELECT id FROM #${dao.query.baseTableRow.tableName} WHERE parent_id IS NULL AND organization_id = 1""".as[Int]))
    dao.cacheGetRoots(1).map(i => i.id).toSet shouldEqual roots.toSet

  }

  test("test find all cache values") {
    val categories: Seq[DataCategory] = waitFor(dao.findAllInOrganization(1L))

    categories.foreach { c =>
      val cachedCopy = dao.cacheGet(1, c.id)
      cachedCopy should be(a[Some[_]])
      c.fidesKey shouldEqual cachedCopy.get.fidesKey

    }

  }

  test("test mergeAndReduce") {
    //children are reduced
    dao.mergeAndReduce(1, Set("customer_content_data", "credentials")) shouldEqual Set("customer_content_data")
    dao.mergeAndReduce(1, Set("customer_content_data", "credentials", "personal_genetic_data")) shouldEqual Set(
      "customer_content_data"
    )
    dao.mergeAndReduce(1, Set("credentials", "customer_content_data", "personal_genetic_data")) shouldEqual Set(
      "customer_content_data"
    )
    dao.mergeAndReduce(1, Set("credentials", "personal_genetic_data", "customer_content_data")) shouldEqual Set(
      "customer_content_data"
    )
    // complete set is not reduced
    dao.mergeAndReduce(
      1,
      Set(
        "credentials",
        "customer_contact_lists",
        "personal_health_data_and_medical_records",
        "personal_genetic_data",
        "personal_biometric_data",
        "personal_data_of_children",
        "political_opinions",
        "financial_details",
        "sensor_measurement_data"
      )
    ) shouldEqual Set("customer_content_data")

    //incomplete set is not reduced

    dao.mergeAndReduce(
      1,
      Set(
        "credentials",
        "customer_contact_lists",
        "personal_health_data_and_medical_records",
        "personal_genetic_data",
        "personal_biometric_data",
        "personal_data_of_children",
        "political_opinions",
        "financial_details"
      )
    ) shouldEqual Set(
      "credentials",
      "customer_contact_lists",
      "personal_health_data_and_medical_records",
      "personal_genetic_data",
      "personal_biometric_data",
      "personal_data_of_children",
      "political_opinions",
      "financial_details"
    )

    val categories: Seq[String] = dao.cacheGetAll(1).values.map(_.fidesKey).toSeq
    //any 1 element sets are unchanged
    for (i <- 1 to 100) {
      val single: Set[String] = Set(oneOf[String](categories))
      dao.mergeAndReduce(1, single) shouldEqual single
    }
    //any root level values remain, and any children they have are no longer present
    val roots = dao.cacheGetAll(1).values.filter(_.isRoot).map(_.fidesKey).toSeq
    for (i <- 1 to 100) {
      val set: Set[String] = smallSetOf(10, 32, categories)
      val root             = oneOf(roots)
      dao.mergeAndReduce(1, set ++ Set(root)) should contain(root)
    }

    for (i <- 1 to 100) {
      val set: Set[String] = smallSetOf(10, 32, categories)
      val combined         = dao.mergeAndReduce(1, set)
      combined.size should be <= set.size
    }
  }
}
