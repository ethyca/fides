package devtools.rating

import devtools.domain.Approval
import devtools.domain.enums.ApprovalStatus
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class PolicyEvaluatorTest extends AnyFunSuite with TestUtils with BeforeAndAfterAll {

  private val rater    = new PolicyEvaluator(App.ruleRater, App.registryApprovalChecks, App.daos)(App.executionContext)
  private val testData = new RatingTestData()

  override def afterAll(): Unit = {
    testData.destroy()
  }

  test("test rate rating catch missing dataset") {
    val v: Approval = waitFor(rater.systemEvaluate(testData.system3, 1, "test", 1))
    val messages    = v.messages.get
    messages("errors").toSeq should containMatchString(
      "These systems were declared as dependencies but were not found"
    )
    messages("errors").toSeq should containMatchString(
      "These datasets were declared as dependencies but were not found"
    )

    v.status shouldEqual ApprovalStatus.FAIL

  }
  test("test rate registry") {
    val v = waitFor(
      rater.registryEvaluate(
        testData.r1.copy(systems = Some(Right(Seq(testData.system1, testData.system1, testData.system3)))),
        1,
        1
      )
    )
    val messages = v.messages.get
    messages("errors").toSeq should containMatchString("cyclic reference")
  }

}
