package devtools.rating

import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.not
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class EvaluatorTest extends AnyFunSuite with TestUtils with BeforeAndAfterAll {

  private val evaluator = new Evaluator(App.daos)(App.executionContext)
  private val testData  = new RatingTestData()

  override def afterAll(): Unit = {
    testData.destroy()
  }

  test("test retrieve evaluator object") {
    val s1 = testData.s1
    val s2 = testData.s2
    val s3 = testData.s3

    val eo1 = waitFor(evaluator.retrievePopulated(Seq(testData.s1, testData.s2)))
    //eo1 contains populated s1, s2, s3(because it's in system dependencies), referenced datasets
    eo1.systems.keys shouldBe Set(s1, s2, s3).map(_.fidesKey)
    eo1.systems.values.map(_.privacyDeclarations.isDefined) should not contain false
    eo1.datasets.values.map(_.fields.isDefined) should not contain false
    eo1.policies.map(_.rules.isDefined) should not contain false

    //retrieving data from unpopulated systems should yield the same results
    val eo2 = waitFor(
      evaluator.retrievePopulated(
        Seq(testData.s1.copy(privacyDeclarations = None), testData.s2.copy(privacyDeclarations = None))
      )
    )
    //eo2 also contains populated s1, s2, s3(because it's in system dependencies), referenced datasets

    eo2.systems.keys shouldBe Set(s1, s2, s3).map(_.fidesKey)
    eo2.systems.values.map(_.privacyDeclarations.isDefined) should not contain false
    eo2.datasets.values.map(_.fields.isDefined) should not contain false
    eo2.policies.map(_.rules.isDefined) should not contain false

    eo1.systems.size shouldBe eo2.systems.size
    eo1.datasets.size shouldBe eo2.datasets.size
    eo1.policies.size shouldBe eo2.policies.size
  }

}
