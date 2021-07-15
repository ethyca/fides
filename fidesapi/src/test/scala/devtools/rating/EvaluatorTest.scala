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
  //test systems
  private val s1                  = testData.s1
  private val s2                  = testData.s2
  private val s3                  = testData.s3
  private val r1                  = testData.r1
  private val evaluationObjectSet = waitFor(evaluator.retrievePopulated(Seq(testData.s1, testData.s2)))
  override def afterAll(): Unit = {
    testData.destroy()
  }

  test("test retrieve evaluator object") {
    //eo1 contains populated s1, s2, s3(because it's in system dependencies), referenced datasets
    evaluationObjectSet.systems.keys shouldBe Set(s1, s2, s3).map(_.fidesKey)
    evaluationObjectSet.systems.values.map(_.privacyDeclarations.isDefined) should not contain false
    evaluationObjectSet.datasets.values.map(_.fields.isDefined) should not contain false
    evaluationObjectSet.policies.map(_.rules.isDefined) should not contain false

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

    evaluationObjectSet.systems.size shouldBe eo2.systems.size
    evaluationObjectSet.datasets.size shouldBe eo2.datasets.size
    evaluationObjectSet.policies.size shouldBe eo2.policies.size
  }

  test("generate system evaluation") {
    val approval = waitFor(evaluator.systemEvaluate(s1, 1L, None, None))
    prettyPrintJson(approval)
  }

  test("system evaluation dry run") {
    val approval = waitFor(evaluator.systemDryRun(s2, 1L))
    prettyPrintJson(approval)
  }

  test("generate registry evaluation") {
    val approval = waitFor(evaluator.registryEvaluate(r1, 1L, None, None))

    prettyPrintJson(approval)

  }

  test("registry evaluation dry run") {
    val approval = waitFor(evaluator.registryDryRun(r1, 1L))
    prettyPrintJson(approval)
  }
}
