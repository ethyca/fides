package devtools.persist.service

import devtools.domain.policy.PolicyRule
import devtools.persist.dao.PolicyRuleDAO
import devtools.persist.db.Tables.PolicyRuleQuery
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.Validator
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.ExecutionContext

class PolicyRuleService(dao: PolicyRuleDAO)(implicit val context: ExecutionContext)
  extends Service[PolicyRule, Long, PolicyRuleQuery](dao, Validator.noOp[PolicyRule, Long])(context)
  with UniqueKeySearch[PolicyRule, PolicyRuleQuery] {

  def findByUniqueKeyQuery(organizationId: Long, key: String): PolicyRuleQuery => Rep[Boolean] = { t =>
    t.fidesKey === key && t.organizationId === organizationId
  }

}
