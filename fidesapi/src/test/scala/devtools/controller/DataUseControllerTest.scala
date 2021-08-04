package devtools.controller

import devtools.controller.definition.ApiResponse
import devtools.domain.{DataUse, DataUseTree}
import devtools.util.JsonSupport.{dumps => jdumps, parseToObj => jParseToObj}
import devtools.{App, TestUtils}
import org.json4s.native.JsonMethods._
import org.scalatest.BeforeAndAfterAll
import org.scalatra.test.scalatest.ScalatraFunSuite

class DataUseControllerTest extends ScalatraFunSuite with TestUtils with BeforeAndAfterAll with TestHeaders {

  implicit val swagger: DevToolsSwagger = new DevToolsSwagger
  val path                              = "/v1/data-use"
  addServlet(App.dataUseController, path)

  test(s"GET $path/taxonomy should return non-empty taxonomy") {
    get(s"$path/taxonomy", headers = testHeaders) {
      status should equal(200)
      val c = parse(body).extract[ApiResponse[Seq[DataUseTree]]]
      assert(c.data.nonEmpty)
      assert(c.errors.isEmpty)
    }
  }
  test("test validations on insert") {
    val newKey  = faker.Name.last_name
    val dataUse = DataUse(0, None, randomInt, newKey, None, None, None, None)

    post(path, jdumps(dataUse), withTestHeaders("Content-Type" -> "application/json")) {
      val response = jParseToObj[ApiResponse[DataUse]](body)
      response.get.errors should containMatchString("organizationId")
    }
  }
  override def header: Null = null
}
