package devtools.controller

import devtools.controller.definition.{BaseController, LongPK}
import devtools.domain.Approval
import devtools.persist.dao.UserDAO
import devtools.persist.service.ApprovalService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.scalate.ScalateSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class ApprovalController(val service: ApprovalService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[Approval, Long] with LongPK[Approval] with ScalateSupport {
  val yamlFormat: YamlFormat[Approval] = FidesYamlProtocols.ApprovalFormat

}
