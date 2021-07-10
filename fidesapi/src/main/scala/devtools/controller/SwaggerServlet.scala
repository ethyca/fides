package devtools.controller

import org.scalatra.ScalatraServlet
import org.scalatra.swagger._
object DevToolsApiInfo
  extends ApiInfo(
    "DevTools API",
    "Documentation for DevTools API",
    "http://scalatra.org",
    ContactInfo("apiteam", "http://foo", "apiteam@scalatra.org"),
    LicenseInfo("MIT", "http://opensource.org/licenses/MIT")
  ) {}

class DevToolsSwagger extends Swagger(Swagger.SpecVersion, "1.0.0", DevToolsApiInfo)

class SwaggerServlet(implicit val swagger: Swagger) extends ScalatraServlet with NativeSwaggerBase
