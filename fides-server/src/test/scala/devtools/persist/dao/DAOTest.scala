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

class DAOTest extends AnyFunSuite with BeforeAndAfterAll with LazyLogging with TestUtils {

  implicit val executionContext: ExecutionContextExecutor = App.executionContext

  test("test pagination") {
    // for pagination we'll use data categories, since they have
    // the largest pre-population of setup data (about 40+ values)
    val dao = App.dataCategoryDAO
    //first 5, sorted by id
    //  val values = waitFor(dao.getAll(_.id, 5, 0))

  }

  test("test filter paginated") {}

}
