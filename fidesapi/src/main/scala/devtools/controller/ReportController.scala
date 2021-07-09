package devtools.controller

import devtools.controller.definition.ApiResponse.asyncResponse
import devtools.controller.definition.{AuthenticationSupport, ControllerSupport}
import devtools.domain.ReportLine
import devtools.persist.dao.UserDAO
import devtools.persist.service.ReportService
import devtools.util.JsonSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class ReportController(val service: ReportService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  val executor: ExecutionContext
) extends ControllerSupport with AuthenticationSupport {

  override protected def applicationDescription: String = "Reporting API"

  get(
    "/",
    operation(
      apiOperation[ReportLine](s"find all operations for the calling organization")
    )
  )(asyncResponse(service.organizationReport(requestContext))(executor, scalatraContext, JsonSupport.formats))

  get(
    "/system/:id",
    operation(
      apiOperation[ReportLine](s"find all operations for the specified system")
        .parameters(pathParam[Int]("id").description(s"System id"))
    )
  )(
    withIntParameter(
      params("id"),
      request,
      (id, _) =>
        asyncResponse(
          service.systemReport(id, requestContext)
        )(executor, scalatraContext, JsonSupport.formats)
    )
  )

  get(
    "/registry/:id",
    operation(
      apiOperation[ReportLine](s"find all operations for the specified registry")
        .parameters(pathParam[Int]("id").description(s"Registry id"))
    )
  )(
    withIntParameter(
      params("id"),
      request,
      (id, _) =>
        asyncResponse(
          service.registryReport(id, requestContext)
        )(executor, scalatraContext, JsonSupport.formats)
    )
  )

}
