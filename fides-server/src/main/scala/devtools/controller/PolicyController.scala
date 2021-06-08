package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.policy.Policy
import devtools.persist.dao.UserDAO
import devtools.persist.service.PolicyService
import devtools.util.ConfigLoader.requiredProperty
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra._
import org.scalatra.servlet.{FileUploadSupport, MultipartConfig, SizeConstraintExceededException}
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class PolicyController(val service: PolicyService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[Policy, Long] with FileUploadSupport with LongPK[Policy] with GetByUniqueKey[Policy] {

  val yamlFormat: YamlFormat[Policy]           = FidesYamlProtocols.PolicyFormat
  override val inputMergeMap: Map[String, Any] = Map("id" -> 0L, "creationTime" -> null, "lastUpdateTime" -> null)

  configureMultipartHandling(
    MultipartConfig(maxFileSize = Some(requiredProperty[Long]("fides.file.upload.max.bytes")))
  )
  error {
    case e: SizeConstraintExceededException => RequestEntityTooLarge(s"too much! ${e.getMessage}")
  }

}
