package devtools.persist.service

import devtools.domain.policy.PolicyRule
import devtools.persist.dao.PolicyRuleDAO
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class PolicyRuleService(dao: PolicyRuleDAO)(implicit val context: ExecutionContext)
  extends Service[PolicyRule, Long](dao, Validator.noOp[PolicyRule, Long])(context) with UniqueKeySearch[PolicyRule] {

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[PolicyRule]] =
    dao.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)

}
