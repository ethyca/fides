package devtools.rating

import devtools.{App, TestUtils}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.concurrent.ExecutionContext

class RegistryEvaluatorTest extends AnyFunSuite with TestUtils {

  implicit val context: ExecutionContext = App.executionContext
  private val systemEvaluator            = new SystemEvaluator(App.daos)
  private val registryEvaluator          = new RegistryEvaluator(systemEvaluator)

  test("test cycle check") {

    //a->b->c->d->e->a
    registryEvaluator.cycleCheck(
      Seq(
        systemOf("a").copy(systemDependencies = Set("b")),
        systemOf("b").copy(systemDependencies = Set("c")),
        systemOf("c").copy(systemDependencies = Set("d")),
        systemOf("d").copy(systemDependencies = Set("e")),
        systemOf("e").copy(systemDependencies = Set("a"))
      )
    ) should containMatchString("cyclic reference")

  }

}
