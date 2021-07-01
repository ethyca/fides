package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.Generators.{blankSystem, fidesKey, randomText, requestContext}
import devtools.domain.enums.AuditAction.{CREATE, DELETE, UPDATE}
import devtools.domain.{AuditLog, Registry}
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.concurrent.ExecutionContext

class RegistryServiceTest extends AnyFunSuite with LazyLogging with TestUtils with BeforeAndAfterAll {
  private val systemDAO                           = App.systemDAO
  private val registryService                     = App.registryService
  implicit val executionContext: ExecutionContext = App.executionContext

  private var sys1 =
    blankSystem.copy(organizationId = 1, fidesKey = fidesKey, name = Some("child1"), description = Some(randomText()))
  private var sys2               = sys1.copy(fidesKey = fidesKey, name = Some("child2"), description = Some(randomText()))
  private var sys3               = sys2.copy(fidesKey = fidesKey, name = Some("child3"), description = Some(randomText()))
  private val registry: Registry = Registry(0, 1, fidesKey, None, None, None, None, None, None, None)

  override def beforeAll(): Unit = {
    sys1 = waitFor(systemDAO.create(sys1))
    sys2 = waitFor(systemDAO.create(sys2))
    sys3 = waitFor(systemDAO.create(sys3))
  }
  override def afterAll(): Unit = {
    for (sys <- Seq(sys1, sys2, sys3)) {
      systemDAO.delete(sys.id)
    }
  }

  private def systemRegistryId(systemId: Long) = waitFor(systemDAO.findById(systemId).map(_.get.registryId))

  test("test registry composite insert") {
    val startVersion = currentVersionStamp(1)

    //create a base with base c1, c2
    val insertedRegistry: Registry = waitFor(
      registryService.create(registry.copy(systems = Some(Left(Seq(sys1.id, sys2.id)))), requestContext)
    )

    systemRegistryId(sys1.id) should be(Some(insertedRegistry.id))
    systemRegistryId(sys2.id) should be(Some(insertedRegistry.id))
    systemRegistryId(sys3.id) should be(None)

    //version stamp has updated
    insertedRegistry.versionStamp.get should be > startVersion
    val afterCreateVersion = currentVersionStamp(1)
    afterCreateVersion should be > startVersion
    val logRecord: Seq[AuditLog] = waitFor(findAuditLogs(insertedRegistry.id, "Registry", CREATE))
    logRecord.size shouldEqual 1
    logRecord.head.versionStamp shouldEqual insertedRegistry.versionStamp

    val updateInput = insertedRegistry.copy(systems = Some(Left(Seq(sys2.id, sys3.id))))
    val updatedResponse = waitFor(
      registryService
        .update(updateInput, requestContext)
        .flatMap(_ => registryService.findById(insertedRegistry.id, requestContext))
    ).get
    systemRegistryId(sys1.id) should be(None)
    systemRegistryId(sys2.id) should be(Some(insertedRegistry.id))
    systemRegistryId(sys3.id) should be(Some(insertedRegistry.id))
    //version stamp has updated
    updatedResponse.versionStamp.get should be > afterCreateVersion
    val afterUpdateVersion = currentVersionStamp(1)
    afterUpdateVersion should be > afterCreateVersion
    val logRecord2: Seq[AuditLog] = waitFor(findAuditLogs(insertedRegistry.id, "Registry", UPDATE))
    logRecord2.size shouldEqual 1
    logRecord2.head.versionStamp shouldEqual updatedResponse.versionStamp

    //delete should increment the org version
    waitFor(registryService.delete(insertedRegistry.id, requestContext))
    // we should have 1 delete record in the audit log
    waitFor(findAuditLogs(insertedRegistry.id, "Registry", DELETE)).size shouldEqual 1
    //Systems are not deleted but have their registry ids unset
    systemRegistryId(sys1.id) should be(None)
    systemRegistryId(sys2.id) should be(None)
    systemRegistryId(sys3.id) should be(None)
    currentVersionStamp(1) should be > afterUpdateVersion
  }

}
