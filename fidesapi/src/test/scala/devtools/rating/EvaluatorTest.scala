package devtools.rating

import devtools.domain.Approval
import devtools.domain.enums.ApprovalStatus
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class EvaluatorTest extends AnyFunSuite with TestUtils with BeforeAndAfterAll {

  private val evaluator = new Evaluator(App.daos)(App.executionContext)
  private val testData  = new RatingTestData()

  override def afterAll(): Unit = {
    testData.destroy()
  }

  test("test populates") {
    // true shouldBe( false)

  }

}
