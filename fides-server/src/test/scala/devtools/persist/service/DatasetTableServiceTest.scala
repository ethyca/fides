package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.Generators.{fidesKey, randomText, requestContext}
import devtools.domain.{DatasetField, DatasetTable}
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.concurrent.ExecutionContext

class DatasetTableServiceTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {

  private val datasetFieldDAO                     = App.datasetFieldDAO
  private val datasetTableService                 = App.datasetTableService
  implicit val executionContext: ExecutionContext = App.executionContext

  def findChildByNameFromDb(name: String, children: Option[Seq[DatasetField]]): Option[DatasetField] = {
    val child = children.getOrElse(Seq()).find(_.name == name)
    child.flatMap(field => waitFor(datasetFieldDAO.findById(field.id)))
  }

  def matchChild(p: DatasetTable, name: String, comparison: (DatasetField, DatasetField) => Boolean): Unit =
    p.fields.flatMap(_.find(_.name == name)) match {
      case Some(rule) =>
        val dbValue = waitFor(datasetFieldDAO.findById(rule.id)).get
        comparison(rule, dbValue) shouldEqual true

      case _ =>
        fail(s"No dataset rule found with name $name")

    }
  private val r1                  = DatasetField(0, 0, "child1", Some(randomText()), None, None, None, None)
  private val r2                  = r1.copy(name = "child2", description = Some(randomText()))
  private val r3                  = r1.copy(name = "child3", description = Some(randomText()))
  private val table: DatasetTable = DatasetTable(0, 1, fidesKey, None, None, None, None)
  test("test table composite insert") {

    //create a base with base c1, c2
    val response = waitFor(
      datasetTableService.create(table.copy(fields = Some(Seq(r1, r2))), requestContext)
    )
    //validate that all 3 children exist
    matchChild(response, r1.name, (a, b) => a.description == b.description)
    matchChild(response, r1.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
    matchChild(response, r2.name, (a, b) => a.description == b.description)
    matchChild(response, r2.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)

    val updateInput = response.copy(fields = Some(Seq(r2, r3)))
    val updatedResponse = waitFor(
      datasetTableService
        .update(updateInput, requestContext)
        .flatMap(_ => datasetTableService.findById(response.id, requestContext))
    ).get

    //update base to c2, c3
    matchChild(updatedResponse, r2.name, (a, b) => a.description == b.description)
    matchChild(updatedResponse, r2.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
    matchChild(updatedResponse, r3.name, (a, b) => a.description == b.description)
    matchChild(updatedResponse, r3.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
    // child1 does not exist
    findChildByNameFromDb("child1", response.fields) shouldEqual None

    //delete should increment the org version
    waitFor(datasetTableService.delete(response.id, requestContext))
    // we should have 1 delete record in the audit log
    findChildByNameFromDb("child1", response.fields) shouldEqual None
    findChildByNameFromDb("child2", updatedResponse.fields) shouldEqual None
    findChildByNameFromDb("child3", updatedResponse.fields) shouldEqual None

  }

}
