package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.Generators.{DeclarationGen, PolicyGen, blankSystem, requestContext}
import devtools.domain.Approval
import devtools.domain.enums.AuditAction.{CREATE, DELETE, UPDATE}
import devtools.domain.enums.PolicyAction.REJECT
import devtools.domain.enums.RuleInclusion.{ALL, ANY, NONE}
import devtools.domain.enums._
import devtools.domain.policy.Declaration
import devtools.persist.dao.{AuditLogDAO, OrganizationDAO, SystemDAO}
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.collection.mutable
import scala.concurrent.ExecutionContext

class SystemServiceTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {
  val systemService: SystemService                = App.systemService
  val policyService: PolicyService                = App.policyService
  val systemDAO: SystemDAO                        = App.systemDAO
  val orgDAO: OrganizationDAO                     = App.organizationDAO
  val auditLogDAO: AuditLogDAO                    = App.auditLogDAO
  implicit val executionContext: ExecutionContext = App.executionContext
  val systemIds: mutable.Set[Long]                = mutable.HashSet[Long]()

  override def afterAll(): Unit = {
    systemIds.foreach(systemDAO.delete)
  }

  test("test crud operations set versions and audit logs") {

    val v =
      waitFor(systemService.create(blankSystem.copy(declarations = Seq(DeclarationGen.sample.get)), requestContext))

    // we should have 1 create record in the audit log
    waitFor(auditLogDAO.find(v.id, "SystemObject", CREATE)).size shouldEqual 1

    systemIds.add(v.id)

    waitFor(systemService.update(v.copy(description = Some("description")), requestContext))
    val updatedResponse = waitFor(systemService.findById(v.id, requestContext)).get

    updatedResponse.description shouldEqual Some("description")

    // we should have 1 update record in the audit log
    waitFor(auditLogDAO.find(v.id, "SystemObject", UPDATE)).size shouldEqual 1

    //delete should increment the org version

    waitFor(systemService.delete(v.id, requestContext))
    // we should have 1 delete record in the audit log
    waitFor(auditLogDAO.find(v.id, "SystemObject", DELETE)).size shouldEqual 1

  }

}
