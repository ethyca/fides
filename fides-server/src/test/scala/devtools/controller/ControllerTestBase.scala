package devtools.controller

import devtools.Generators.requestContext
import devtools.TestUtils
import devtools.controller.definition.{ApiResponse, BaseController}
import devtools.domain.definition.IdType
import devtools.util.JsonSupport.{dumps => jdumps, parseToObj => jParseToObj, toAST => jToAST}
import devtools.util.YamlSupport.{dumps => ydumps, toAST => yToAST}
import devtools.util.{FidesYamlProtocols, JsonSupport}
import org.scalacheck.Gen
import org.scalatest.{Assertion, BeforeAndAfterAll}
import org.scalatra.test.scalatest._

import scala.collection.mutable.{HashSet => MHashSet}
import scala.util.{Failure, Success, Try}

abstract class ControllerTestBase[T <: IdType[T, PK], PK](
  val path: String,
  val generator: Gen[T],
  val controller: BaseController[T, PK]
)(implicit manifest: Manifest[T])
  extends ScalatraFunSuite with TestUtils with BeforeAndAfterAll with TestHeaders {

  val ids: MHashSet[PK] = new MHashSet[PK]
  /** Cleanup any created records */
  override def afterAll(): Unit = {
    ids.foreach(id => controller.service.delete(id, requestContext))
  }
  implicit val swagger: DevToolsSwagger = new DevToolsSwagger

  val typeName: String = manifest.runtimeClass.getSimpleName
  /** Define some way to edit a value that will still be a valid update. This is used in testing CRUD operations */
  def editValue(t: T): T
  def isValid(t: T): Boolean

  /** Domain object less merge map values, expressed as a map */
  def withoutMergeValues(t: T): Map[String, Any] =
    toMap[T](t).filter { case (k, _) => !controller.inputMergeMap.contains(k) }

  def compareWithoutMergeValues(left: T, right: T): Assertion = {
    val l    = withoutMergeValues(left) ++ controller.inputMergeMap
    val lobj = jParseToObj(JsonSupport.dumps(l))
    val r    = withoutMergeValues(right) ++ controller.inputMergeMap
    val robj = jParseToObj(JsonSupport.dumps(r))
    lobj shouldEqual robj
  }

  def shouldBe200(status: Int, body: String): Assertion = {
    if (status != 200) {
      System.err.println(s"RESPONDED WITH STATUS=$status, BODY=[$body]")
    }
    status shouldEqual 200
  }
  addServlet(controller, s"/$path")

  test(testName = s"Test /$path Crud API") {
    var testInstance: T = generator.sample.get

    post(s"/$path", jdumps(withoutMergeValues(testInstance)), withTestHeaders("Content-Type" -> "application/json")) {

      shouldBe200(status, body)
      val returned: Try[T] = parseBody[T](body)
      returned should be(a[Success[_]])
      //returned instance is == excluding id
      compareWithoutMergeValues(returned.get, testInstance)
      testInstance = returned.get
      ids.add(testInstance.id)
    }

    get(s"/$path/${testInstance.id}", headers = testHeaders) {
      shouldBe200(status, body)
      val returned: Try[T] = parseBody[T](body)
      compareWithoutMergeValues(returned.get, testInstance)

    }
    get(s"/$path", headers = testHeaders) {
      shouldBe200(status, body)
      val all = jParseToObj[ApiResponse[List[T]]](body).get.data.get
      assert(all.nonEmpty)
      assert(all.forall(isValid))
    }
    testInstance = editValue(testInstance)
    post(s"/$path/${testInstance.id}", jdumps(testInstance), withTestHeaders("Content-Type" -> "application/json")) {
      shouldBe200(status, body)
      val returned: Try[T] = parseBody[T](body)
      compareWithoutMergeValues(returned.get, testInstance)
    }
    get(s"/$path/${testInstance.id}", headers = testHeaders) {
      compareWithoutMergeValues(parseBody[T](body).get, testInstance)
    }
    delete(s"/$path/${testInstance.id}", headers = testHeaders) {
      shouldBe200(status, body)
    }
    get(s"/$path/${testInstance.id}", headers = testHeaders) {
      status should equal(404) //TODO Not found should return 404; bad id should return 400
    }
    testInstance = generator.sample.get
    //post as yaml
    post(
      s"/$path",
      ydumps(yToAST(testInstance)(controller.yamlFormat)),
      withTestHeaders("Content-Type" -> "application/yaml")
    ) {
      shouldBe200(status, body)
      val returned: Try[T] = parseBody(body)
      returned should be(a[Success[_]])
      //returned instance is == excluding id
      compareWithoutMergeValues(returned.get, testInstance)
      testInstance = returned.get
      ids.add(testInstance.id)
    }
    delete(s"/$path/${testInstance.id}", headers = testHeaders) {
      shouldBe200(status, body)
    }
  }

//setup for json and yaml tests
  val instance: T                     = generator.sample.get
  val instanceAsMap: Map[String, Any] = toMap[T](instance)
  val woMergeValues: Map[String, Any] = instanceAsMap.filter { case (k, _) => !controller.inputMergeMap.contains(k) }

  test(s"test parse json $typeName") {
    val defaultInputValues = controller.inputMergeMap
    // remove merge map values
    val inputString    = jdumps(jToAST(woMergeValues))
    val parsed: Try[T] = controller.ingest(inputString, "application/json", defaultInputValues)
    parsed should be(a[Success[_]]) //
    toMap[T](parsed.get).filter { t => !defaultInputValues.contains(t._1) } shouldEqual woMergeValues
    //parsing with missing fields should fail
    val reducedParsed: Try[T] = controller.ingest("{}", "application/json", defaultInputValues)
    reducedParsed should be(a[Failure[_]])
    // raw jvalue parseable should fail
    controller.ingest("raw string", "application/json", defaultInputValues) should be(a[Failure[_]])
  }

  test(s"test parse yaml $typeName") {
    val defaultInputValues = controller.inputMergeMap
    // remove merge map values
    val inputString    = ydumps(yToAST(woMergeValues)(FidesYamlProtocols.MapAnyFormat))
    val parsed: Try[T] = controller.ingest(inputString, "application/yaml", defaultInputValues)
    parsed should be(a[Success[_]]) //
    toMap[T](parsed.get).filter { t => !defaultInputValues.contains(t._1) } shouldEqual woMergeValues
    //parsing with missing fields should fail
    val reducedParsed: Try[T] = controller.ingest("{}", "application/yaml", defaultInputValues)
    reducedParsed should be(a[Failure[_]])
    // raw jvalue parseable should fail
    controller.ingest("raw string", "application/yaml", defaultInputValues) should be(a[Failure[_]])
  }
  override def header: Null = null
}
