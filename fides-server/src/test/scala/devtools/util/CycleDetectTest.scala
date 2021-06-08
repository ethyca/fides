package devtools.util

import devtools.TestUtils
import devtools.util.CycleDetector.{NodeValue, collectCycleErrors}
import devtools.validation.MessageCollector
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class CycleDetectTest extends AnyFunSuite with TestUtils {

  private def hasCycles(keys: Seq[NodeValue]): Seq[String] = {
    val errorCollector = new MessageCollector()
    collectCycleErrors(keys, errorCollector)
    errorCollector.errors.toList
  }

  test("test cycle detection") {
    hasCycles(Seq(("A", Set("B")), ("B", Set("C")), ("C", Set("A")), ("D", Set("C")))) should containMatchString(
      "A->B->C->A"
    )
    hasCycles(Seq(("D", Set("C")), ("A", Set("B")), ("B", Set("C")), ("C", Set("A")))) should containMatchString(
      "C->A->B->C"
    )
    hasCycles(Seq(("A", Set("B")), ("B", Set("A")))) should containMatchString("A->B")
    hasCycles(
      Seq(
        ("A", Set("B")),
        ("B", Set("C")),
        ("C", Set("D")),
        ("D", Set("E")),
        ("E", Set("F")),
        ("F", Set("A")),
        ("Z", Set())
      )
    ) should containMatchString("A->B->C->D->E")
    hasCycles(Seq(("A", Set("A")))) should containMatchString("A->A")
    //should also work with bad nodes:
    hasCycles(
      Seq(
        ("A", Set("B")),
        ("B", Set("C")),
        ("C", Set("D", "X1", "X2", "X3", "X4")),
        ("D", Set("E", "X1", "X2", "X3", "X4")),
        ("E", Set("F", "X2", "X3")),
        ("F", Set("A", "X1", "X2")),
        ("Z", Set())
      )
    ) should containMatchString("A->B->C->D->E")
  }

}
