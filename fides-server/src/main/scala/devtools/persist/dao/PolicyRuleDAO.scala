package devtools.persist.dao
import devtools.domain.policy.PolicyRule
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{PolicyRuleQuery, policyRuleQuery}
import slick.dbio.Effect
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._
import slick.sql.FixedSqlAction

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}
class PolicyRuleDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[PolicyRule, Long, PolicyRuleQuery](policyRuleQuery) with AutoIncrementing[PolicyRule, PolicyRuleQuery]
  with ByOrganizationDAO[PolicyRule, PolicyRuleQuery] {

  override implicit def getResult: GetResult[PolicyRule] =
    r =>
      PolicyRule.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[String],
        r.<<?[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<?[String],
        r.<<[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )
  def getPolicyRules(policyId: Long): Future[Seq[PolicyRule]] = runAction(query.filter(_.policyId === policyId).result)

  override def createAction(record: PolicyRule): FixedSqlAction[PolicyRule, NoStream, Effect.Write] =
    insertQuery += record.copy(id = 0, creationTime = None, lastUpdateTime = None)
  /** i.e   select * from policy_rule where JSON_SEARCH(data_uses, 'one', 'provide', NULL, '$.values') IS NOT NULL; */
  def findPolicyRuleWithDataUse(organizationId: Long, fidesKey: String): Future[Seq[Long]] =
    db.run(
      sql"""select id FROM POLICY_RULE WHERE organization_id = #$organizationId AND JSON_SEARCH(data_uses, 'one','#$fidesKey',NULL, '$$.values' ) IS NOT NULL"""
        .as[Long]
    )

  def findPolicyRuleWithDataQualifer(organizationId: Long, fidesKey: String): Future[Seq[Long]] =
    db.run(
      query.filter(p => { p.organizationId === organizationId && (p.dataQualifier === fidesKey) }).map(_.id).result
    )

  def findPolicyRuleWithDataCategory(organizationId: Long, fidesKey: String): Future[Seq[Long]] =
    db.run(
      sql"""select id FROM POLICY_RULE WHERE organization_id = #$organizationId AND JSON_SEARCH(data_categories, 'one','#$fidesKey',NULL, '$$.values' ) IS NOT NULL"""
        .as[Long]
    )

  def findPolicyRuleWithSubject(organizationId: Long, fidesKey: String): Future[Seq[Long]] =
    db.run(
      sql"""select id FROM POLICY_RULE WHERE organization_id = #$organizationId AND JSON_SEARCH(data_subjects, 'one','#$fidesKey',NULL, '$$.values' ) IS NOT NULL"""
        .as[Long]
    )
  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): PolicyRuleQuery => Rep[Option[Boolean]] = {
    t: PolicyRuleQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value) ||
      (t.dataUses like value) ||
      (t.dataSubjects like value) ||
      (t.dataQualifier like value) ||
      (t.action like value)
  }

}
