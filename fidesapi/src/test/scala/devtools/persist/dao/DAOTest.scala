package devtools.persist.dao

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.AuditLog
import devtools.domain.enums.AuditAction
import devtools.util.{Pagination, waitFor}
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.PostgresProfile.api._

import scala.collection.mutable.{HashSet => HSet}

class DAOTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {

  private val ids: HSet[Long] = new HSet[Long]

  // for pagination we'll use audit log values

  private val dao: AuditLogDAO = App.auditLogDAO
  private val auditActions     = AuditAction.values.toList
  override def beforeAll(): Unit = {

    (1 to 30).foreach(i => {
      val auditLog: AuditLog = waitFor(dao.create(auditLogOf(i.longValue(), auditActions(i % 3), s"test-instance-$i")))
      ids.add(auditLog.id)
    })
  }
  override def afterAll(): Unit = {
    //    dao.delete(_.id inSet (ids.toSet))
  }

  test("test pagination") {
    val setA: Seq[Long] = waitFor(dao.findAllInOrganization(1L, Pagination(10))).map(_.id).sorted
    val setB: Seq[Long] = waitFor(dao.findAllInOrganization(1L, Pagination(10, 10))).map(_.id).sorted
    val setC: Seq[Long] = waitFor(dao.findAllInOrganization(1L, Pagination(10, 20))).map(_.id).sorted

    setA.size shouldEqual 10
    setB.size shouldEqual 10
    setC.size shouldEqual 10
    // values are
    setA.max should be < setB.min
    setB.max should be < setC.min

  }

  test("test filter paginated") {
    val testAction = auditActions.head
    val setA       = waitFor(dao.filterPaginated(_.action === testAction.toString, _.id, Pagination(5)))
    val setB       = waitFor(dao.filterPaginated(_.action === testAction.toString, _.id, Pagination(5, 5)))
    setA.size shouldEqual 5
    setB.size shouldEqual 5

    setA.map(_.id).max should be < setB.map(_.id).min
    setA.map(_.action).toSet shouldEqual Set(testAction)
    setB.map(_.action).toSet shouldEqual Set(testAction)

  }

}
