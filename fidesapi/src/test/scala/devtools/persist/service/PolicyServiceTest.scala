package devtools.persist.service
import com.typesafe.scalalogging.LazyLogging
import devtools.Generators.{fidesKey, randomText, requestContext}
import devtools.domain.AuditLog
import devtools.domain.enums.AuditAction.{CREATE, DELETE, UPDATE}
import devtools.domain.enums.PolicyAction.ACCEPT
import devtools.domain.enums.RuleInclusion.ALL
import devtools.domain.enums._
import devtools.domain.policy._
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.{a, be}
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.PostgresProfile.api._

class PolicyServiceTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {
  private val policyRuleDAO = App.policyRuleDAO
  private val policyService = App.policyService

  def findChildByNameFromDb(name: String): Option[PolicyRule] = waitFor(policyRuleDAO.findFirst(_.name === name))

  def matchChild(p: Policy, ruleName: String, comparison: (PolicyRule, PolicyRule) => Boolean): Unit =
    p.rules.flatMap(_.find(_.name.contains(ruleName))) match {
      case Some(rule) =>
        val dbValue = waitFor(policyRuleDAO.findById(rule.id)).get
        comparison(rule, dbValue) shouldEqual true

      case _ =>
        fail(s"No policy rule found with name $ruleName")
    }

  private val blankGrouping = PolicyValueGrouping(ALL, Set())
  private val rule1 = PolicyRule(
    0,
    1,
    0,
    fidesKey,
    Some("child1"),
    Some(randomText()),
    blankGrouping,
    blankGrouping,
    blankGrouping,
    None,
    ACCEPT,
    None,
    None
  )
  private val rule2          = rule1.copy(fidesKey = fidesKey, name = Some("child2"), description = Some(randomText()))
  private val rule3          = rule1.copy(fidesKey = fidesKey, name = Some("child3"), description = Some(randomText()))
  private val policy: Policy = Policy(0, 1, fidesKey, None, None, None, None, None, None)

  test("test policy composite insert") {
    val startVersion = currentVersionStamp(1)

    //create a base with base c1, c2
    val response = waitFor(
      policyService.create(policy.copy(rules = Some(Seq(rule1, rule2))), requestContext)
    )
    //validate that all 3 children exist
    findChildByNameFromDb(rule1.name.get) should be(a[Some[_]])
    findChildByNameFromDb(rule2.name.get) should be(a[Some[_]])

    //version stamp has updated
    response.versionStamp.get should be > startVersion
    val afterCreateVersion = currentVersionStamp(1)
    afterCreateVersion should be > startVersion
    val logRecord: Seq[AuditLog] = waitFor(findAuditLogs(response.id, "Policy", CREATE))
    logRecord.size shouldEqual 1
    logRecord.head.versionStamp shouldEqual response.versionStamp

    val updateInput = response.copy(rules = Some(Seq(rule2, rule3)))
    val updatedResponse = waitFor(
      policyService
        .update(updateInput, requestContext)
        .flatMap(_ => policyService.findById(response.id, requestContext))
    ).get

    //update base to c2, c3
    matchChild(updatedResponse, rule2.name.get, (a, b) => a.description == b.description)
    matchChild(updatedResponse, rule2.name.get, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
    matchChild(updatedResponse, rule3.name.get, (a, b) => a.description == b.description)
    matchChild(updatedResponse, rule3.name.get, (_, b) => b.creationTime.nonEmpty && b.creationTime == b.lastUpdateTime)
    // child1 does not exist
    findChildByNameFromDb("child1") shouldEqual None

    //version stamp has updated
    updatedResponse.versionStamp.get should be > afterCreateVersion
    val afterUpdateVersion = currentVersionStamp(1)
    afterUpdateVersion should be > afterCreateVersion
    val logRecord2: Seq[AuditLog] = waitFor(findAuditLogs(response.id, "Policy", UPDATE))
    logRecord2.size shouldEqual 1
    logRecord2.head.versionStamp shouldEqual updatedResponse.versionStamp

    //delete should increment the org version
    waitFor(policyService.delete(response.id, requestContext))
    // we should have 1 delete record in the audit log
    waitFor(findAuditLogs(response.id, "Policy", DELETE)).size shouldEqual 1
    findChildByNameFromDb("child1") shouldEqual None
    findChildByNameFromDb("child2") shouldEqual None
    findChildByNameFromDb("child3") shouldEqual None

    currentVersionStamp(1) should be > afterUpdateVersion
  }

}
