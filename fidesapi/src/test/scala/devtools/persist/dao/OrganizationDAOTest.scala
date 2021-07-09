package devtools.persist.dao

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.Organization
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContextExecutor

class OrganizationDAOTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {

  private val dao                                         = App.organizationDAO
  implicit val executionContext: ExecutionContextExecutor = App.executionContext
  test("test increment version counter action") {

    val values = waitFor(dao.runAction((for {
      org: Option[Organization] <- dao.findByIdAction(1)
      v2                        <- dao.getAndIncrementVersionAction(1)
      v3                        <- dao.getAndIncrementVersionAction(1)
      v4                        <- dao.getAndIncrementVersionAction(1)
    } yield (org, v2, v3, v4)).transactionally))

    val startingVersion = values._1.get.versionStamp.get
    val v1Stamp         = values._2.get
    val v2Stamp         = values._3.get
    val v3Stamp         = values._4.get

    v1Stamp should be > startingVersion
    v2Stamp should be > v1Stamp
    v3Stamp should be > v2Stamp

  }

}
