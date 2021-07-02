package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.AuditLogDAO
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.{convertToAnyShouldWrapper, the}
import devtools.Generators._

import scala.collection.mutable
import scala.concurrent.ExecutionContext
class DatasetServiceTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {
  private val datasetService  = App.datasetService
  private val datasetFieldDAO = App.datasetFieldDAO

  private val auditLogDAO: AuditLogDAO            = App.auditLogDAO
  implicit val executionContext: ExecutionContext = App.executionContext
  private val datasetIds: mutable.Set[Long]       = mutable.HashSet[Long]()

  override def afterAll(): Unit = {
    datasetIds.foreach(App.datasetDAO.delete)
  }

  def matchField(
    dataset: Dataset,
    fieldName: String,
    f: (DatasetField, DatasetField) => Boolean
  ): Unit = {
    val field = dataset.fields.getOrElse(Seq()).find(_.name == fieldName)
    field shouldBe Some(_)
    field.map { fld =>
        val dbValue = waitFor(datasetFieldDAO.findById(fld.id)).get
        f(fld, dbValue) shouldEqual true
      }

  }

  test("test dataset composite insert") {

    val f1  = datasetFieldOf(  "f1")
    val f2 =  datasetFieldOf(  "f2")
    val f3  =  datasetFieldOf(  "f3")
    val f4  =  datasetFieldOf(   "f4")
    val ds = datasetOf(fidesKey)
    //create a dataset with tables t1<f1, t2<{f2, f22}, t3<f3, t4<()
    val response = waitFor(datasetService.create(ds, requestContext))


    // response t1 has fields f1      response t2 has fields f2, f3  validate in dao
    matchField(response, t1.name, f1.name, (a, b) => a.description == b.description)
    matchField(response, t2.name, f21.name, (a, b) => a.description == b.description)
    matchField(response, t2.name, f22.name, (a, b) => a.description == b.description)
    matchField(response, t3.name, f3.name, (a, b) => a.description == b.description)

    waitFor(findAuditLogs(response.id, "Dataset", CREATE)).size shouldEqual 1

    datasetIds.add(response.id)

    // a dataset with tables t1<f1(edit), t2<{f2, f22}(unchanged), t3 (omitted) , t4 <f5, t5(new)
    val updateValue = response.copy(
      tables = Some(
        Seq(
          t1.copy(fields =
            Some(Seq(f1.copy(name = "altered_" + f1.name)))
          ),  change the name in an internal field value
          t2, unchanged
          t3 is omitted
          t4.copy(fields = Some(Seq(f5))),
          t5 new table
        )
      )
    )

    val updatedResponse = waitFor(
      datasetService
        .update(updateValue, requestContext)
        .flatMap(_ => datasetService.findById(response.id, requestContext))
    ).get

//    response has tables t1, t2, t3
//    matchTable(updatedResponse, t1.name, (a, b) => a.description == b.description)
//    matchTable(updatedResponse, t1.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
//    matchTable(updatedResponse, t1.name, (_, b) => b.lastUpdateTime.nonEmpty)
//
//    matchTable(updatedResponse, t2.name, (a, b) => a.description == b.description)
//    matchTable(updatedResponse, t2.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
//
//    matchTable(updatedResponse, t4.name, (a, b) => a.description == b.description)
//    matchTable(updatedResponse, t4.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
//
//    matchTable(updatedResponse, t5.name, (a, b) => a.description == b.description)
//    matchTable(updatedResponse, t5.name, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)

    val t3_id = response.tables.get.find(_.name == t3.name).get.id
    waitFor(datasetTableDAO.findById(t3_id)) shouldEqual None

   //  response t1 has fields f1      response t2 has fields f2, f3  validate in dao
    matchField(updatedResponse, t1.name, "altered_" + f1.name, (a, b) => a.name == b.name)
    matchField(updatedResponse, t2.name, f21.name, (a, b) => a.description == b.description)
    matchField(updatedResponse, t2.name, f21.name, (_, b) => b.creationTime == b.lastUpdateTime)
    matchField(updatedResponse, t4.name, f5.name, (a, b) => a.description == b.description)

    // we should have 1 update record in the audit log
    waitFor(findAuditLogs(response.id, "Dataset", UPDATE)).size shouldEqual 1

   // delete should increment the org version
    waitFor(datasetService.delete(response.id, requestContext))
     we should have 1 delete record in the audit log
    waitFor(findAuditLogs(response.id, "Dataset", DELETE)).size shouldEqual 1

  }

}
