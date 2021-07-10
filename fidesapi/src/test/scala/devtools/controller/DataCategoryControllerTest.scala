package devtools.controller

import devtools.App
import devtools.controller.definition.ApiResponse
import devtools.domain.DataCategoryTree
import org.json4s.DefaultFormats
import org.json4s.native.JsonMethods._
import org.scalatra.test.scalatest.ScalatraFunSuite

class DataCategoryControllerTest extends ScalatraFunSuite with TestHeaders {
  implicit val formats: DefaultFormats.type = DefaultFormats
  implicit val swagger: DevToolsSwagger     = new DevToolsSwagger

  addServlet(App.dataCategoryController, "/data-category")

  test("GET /data-category/taxonomy should return non-empty taxonomy") {
    get("/data-category/taxonomy", headers = testHeaders) {
      status should equal(200)

      val c = parse(body).extract[ApiResponse[Seq[DataCategoryTree]]]

      assert(c.data.get.nonEmpty)
    }
  }

  override def header: Null = null
}
