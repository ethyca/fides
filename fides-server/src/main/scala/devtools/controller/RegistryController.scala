package devtools.controller

import devtools.controller.definition.ApiResponse.asyncResponse
import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.{Approval, Registry}
import devtools.persist.dao.UserDAO
import devtools.persist.service.RegistryService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.scalate.ScalateSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success}
class RegistryController(val service: RegistryService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[Registry, Long] with LongPK[Registry] with ScalateSupport with GetByUniqueKey[Registry] {

  val yamlFormat: YamlFormat[Registry] = FidesYamlProtocols.RegistryFormat

  post(
    "/dry-run",
    operation(
      apiOperation[Approval](s"rate a registry")
        .summary(s"submit a registry for approval")
    )
  ) {
    asyncResponse {
      ingest(request.body, request.getHeader("Content-Type"), inputMergeMap) match {
        case Success(t)         => service.dryRun(t, requestContext)
        case Failure(exception) => Future.failed(exception)
      }
    }
  }
}
