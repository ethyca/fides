package devtools.controller.definition

import com.typesafe.scalalogging.LazyLogging
import org.json4s.Formats
import org.scalatra._
import org.scalatra.json._
import org.scalatra.swagger.{Swagger, _}

import javax.servlet.http.HttpServletRequest
import scala.util.{Success, Try}

abstract class ControllerSupport
  extends ScalatraServlet with JacksonJsonSupport with SwaggerSupport with LazyLogging with FutureSupport {
  implicit lazy val jsonFormats: Formats = devtools.util.JsonSupport.formats
  val swagger: Swagger

  before() {
    contentType = formats("json")
  }
  def withIntParameter[Response](
    value: String,
    req: HttpServletRequest,
    f: (Long, HttpServletRequest) => Response
  ): Any = {
    Try { value.trim.toLong } match {
      case Success(id) => f(id, req)
      case _           => ApiResponse.failure(s"parameter ($value) is not an Integer value")
    }
  }

}
