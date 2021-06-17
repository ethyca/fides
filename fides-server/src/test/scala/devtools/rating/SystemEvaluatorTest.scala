package devtools.rating

import devtools.domain.{Approval, Dataset, SystemObject}
import devtools.domain.policy.Policy
import devtools.util.waitFor
import devtools.{App, TestUtils}
import org.scalatest.funsuite.AnyFunSuite

import scala.concurrent.{ExecutionContext, Future}
import slick.jdbc.MySQLProfile.api._
class SystemEvaluatorTest extends AnyFunSuite with TestUtils {

  implicit val context: ExecutionContext = App.executionContext
  private val systemEvaluator            = new SystemEvaluator(App.daos)
  private val testData                   = new RatingTestData()

  private def relatedValues(sys: SystemObject): Future[(Iterable[Policy], Seq[SystemObject], Iterable[Dataset])] =
    for {
      policies         <- App.daos.policyDAO.findHydrated(_.organizationId === sys.organizationId)
      dependentSystems <- App.daos.systemDAO.findForFidesKeyInSet(sys.systemDependencies, sys.organizationId)
      datasets         <- App.daos.datasetDAO.findHydrated(_.fidesKey inSet sys.datasets)
    } yield (policies, dependentSystems, datasets)

  test("test rate rating catch missing dataset") {
//    val rv = waitFor(relatedValues(testData.system3))
//    val v: Approval = waitFor(systemEvaluator.evaluateSystem(testData.system3, rv._2, rv._3.toSeq, rv._1.toSeq)
//    val m = v.details.get
//    val messages = v.messages.get
//    println(s"$m\n\n$messages")
////    messages("errors").toSeq should containMatchString(
//      "These systems were declared as dependencies but were not found"
//    )
//    messages("errors").toSeq should containMatchString(
//      "These datasets were declared as dependencies but were not found"
//    )
//
//    v.status shouldEqual ApprovalStatus.FAIL

  }
  test("test rate registry") {
//    val v = waitFor(
//      evaluator.registryEvaluate(
//        testData.r1.copy(systems = Some(Right(Seq(testData.system1, testData.system1, testData.system3)))),
//        1
//      )
//    )
//
//    prettyPrintJson(v)
//    val messages = v.messages.get
//    messages("errors").toSeq should containMatchString("cyclic reference")
  }

  test("check dependent dataset privacy gamut") {}
  test("check dependent system privacy gamut") {}

  test("check dependent dataset exists") {}
  test("check dependent system exists") {}

  test("test evaluate policy rules") {}

}
