package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.policy.PolicyRule
import devtools.persist.dao.UserDAO
import devtools.persist.service.PolicyRuleService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class PolicyRuleController(val service: PolicyRuleService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[PolicyRule, Long] with LongPK[PolicyRule] with GetByUniqueKey[PolicyRule] {

  val yamlFormat: YamlFormat[PolicyRule] = FidesYamlProtocols.PolicyRuleFormat

  /** Default input values that are part of system object but we don't expect as part of the post */

  override val inputMergeMap = Map("id" -> 0L, "creationTime" -> null, "lastUpdateTime" -> null)

}
