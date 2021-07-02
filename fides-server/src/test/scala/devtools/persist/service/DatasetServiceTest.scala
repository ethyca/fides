package devtools.persist.service
import com.typesafe.scalalogging.LazyLogging
import devtools.Generators._
import devtools.domain.enums.AuditAction._
import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.AuditLogDAO
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.MySQLProfile.api._

import scala.collection.mutable
import scala.concurrent.ExecutionContext
class DatasetServiceTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {
  private val datasetService                      = App.datasetService
  private val datasetFieldDAO                     = App.datasetFieldDAO
  implicit val executionContext: ExecutionContext = App.executionContext
  private val datasetIds: mutable.Set[Long]       = mutable.HashSet[Long]()

  override def afterAll(): Unit = {
    datasetIds.foreach(App.datasetDAO.delete)
  }

  /** match a field against db-stored value, retrieved by field id. */
  def matchField(
    dataset: Dataset,
    fieldName: String,
    f: (DatasetField, DatasetField) => Boolean
  ): Unit = {
    val field = dataset.fields.getOrElse(Seq()).find(_.name == fieldName)

    field match {
      case Some(fld) =>
        val dbValue = waitFor(datasetFieldDAO.findById(fld.id)).get
        f(fld, dbValue) shouldEqual true

      case None => fail(s" No field found for field Name $fieldName")
    }
  }

  test("test dataset composite insert") {

    val f1       = datasetFieldOf("f1").copy(description = Some("f1" + fidesKey))
    val f2       = datasetFieldOf("f2").copy(description = Some("f2" + fidesKey))
    val f3       = datasetFieldOf("f3").copy(description = Some("f3" + fidesKey))
    val f4       = datasetFieldOf("f4").copy(description = Some("f4" + fidesKey))
    val ds       = datasetOf(fidesKey, f1, f2, f3)
    val response = waitFor(datasetService.create(ds, requestContext))

    matchField(response, f1.name, (a, b) => a.description == b.description)
    matchField(response, f2.name, (a, b) => a.description == b.description)
    matchField(response, f3.name, (a, b) => a.description == b.description)

    waitFor(findAuditLogs(response.id, "Dataset", CREATE)).size shouldEqual 1

    datasetIds.add(response.id)

    val updateValue = response.copy(
      fields = Some(
        Seq(
          f1.copy(description = Some("altered_" + f1.description)),
          f2, //
          //f2 is ommited
          f4
        )
      )
    )

    val updatedResponse = waitFor(
      datasetService
        .update(updateValue, requestContext)
        .flatMap(_ => datasetService.findById(response.id, requestContext))
    ).get

    matchField(
      updatedResponse,
      f1.name,
      (a, b) => a.description == b.description && b.description.contains("altered_" + f1.description)
    )
    matchField(updatedResponse, f2.name, (a, b) => a.description == b.description)
    matchField(updatedResponse, f4.name, (a, b) => a.description == b.description)
    waitFor(datasetFieldDAO.findFirst(_.description === f3.description)) shouldBe None

    // we should have 1 update record in the audit log
    waitFor(findAuditLogs(response.id, "Dataset", UPDATE)).size shouldEqual 1

    // delete should increment the org version
    waitFor(datasetService.delete(response.id, requestContext))

    waitFor(findAuditLogs(response.id, "Dataset", DELETE)).size shouldEqual 1
    val fieldIds = response.fields.getOrElse(Seq()).map(_.id) ++ updatedResponse.fields.getOrElse(Seq()).map(_.id)

    waitFor(datasetFieldDAO.filter(_.id.inSet(fieldIds.toSet))).isEmpty shouldEqual true
  }

}
