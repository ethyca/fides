package devtools.persist.dao

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.AuditLog
import devtools.domain.enums.AuditAction
import devtools.persist.db.Tables.AuditLogQuery
import devtools.util.{Pagination, waitFor}
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.MySQLProfile.api._

import scala.collection.mutable.{HashSet => HSet}
import scala.concurrent.ExecutionContextExecutor

class DAOTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {

  implicit val executionContext: ExecutionContextExecutor = App.executionContext

   val ids: HSet[Long] = new HSet[Long]

  // for pagination we'll use audit log values, since they have

  val dao: AuditLogDAO = App.auditLogDAO

  override def beforeAll(): Unit ={
    (1 to 100).foreach(i => {
      val auditLog: AuditLog = waitFor(dao.create(auditLogOf(i.longValue(), AuditAction.CREATE, s"test-instance-$i")))
      ids.add(auditLog.id)
    }
  }
  override def afterAll(): Unit = {
    dao.delete(_.id inSet (ids.toSet))
  }

  test("test pagination") {
      val setA: Seq[Long] = waitFor(dao.findAllInOrganization(1L, Pagination(10,0))).map(_.id).sorted
      val setB: Seq[Long] = waitFor(dao.findAllInOrganization(1L, Pagination(10,10))).map(_.id).sorted

    setA.size shouldEqual 10
    setB.size shouldEqual 10
    // values are
    setA.max should be  < setB.min




  }

  test("test filter paginated") {}

}
