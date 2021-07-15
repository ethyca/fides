package devtools.validation

import devtools.Generators.requestContext
import devtools.TestUtils
import devtools.domain.definition.IdType
import devtools.exceptions.{BaseFidesException, ValidationException}
import devtools.persist.dao.definition.DAO
import devtools.util.waitFor
import org.scalacheck.Gen
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite

import scala.collection.mutable

abstract class ValidatorTestBase[E <: IdType[E, PK], PK](
  val gen: Gen[E],
  val dao: DAO[E, PK, _],
  val validator: Validator[E, PK]
) extends AnyFunSuite with BeforeAndAfterAll with TestUtils {
  val createdIds: mutable.Set[PK] = mutable.HashSet[PK]()

  override def afterAll(): Unit = createdIds.foreach(dao.delete)

  def createValidationErrors(t: E): Seq[String] =
    waitFor {
      validator.validateForCreate(t, requestContext).map(_ => Seq()).recover {
        case e: ValidationException => e.errors
        case e: Throwable           => Seq(e.getMessage)
      }
    }

  def createValidationErrors(f: E => E): Seq[String] = createValidationErrors(f(gen.sample.get))

  def updateValidationErrors(t: E, existing: E): Seq[String] = {

    waitFor(validator.validateForUpdate(t, existing, requestContext).map(_ => Seq()).recover {
      case e: ValidationException => e.errors
      case e: Throwable           => Seq(e.getMessage)
    })
  }

  def updateValidationErrors(initial: E, attemptedUpdate: E => E): Seq[String] = {
    val created = waitFor(dao.create(initial))
    createdIds.add(created.id)
    waitFor {
      validator.validateForUpdate(attemptedUpdate(initial), created, requestContext).map(_ => Seq()).recover {
        case e: BaseFidesException => e.errors
        case e: Throwable          => Seq(e.getMessage)
      }
    }
  }

  def deleteValidationErrors(t: PK): Seq[String] =
    waitFor(
      dao
        .findById(t)
        .flatMap(e =>
          validator.validateForDelete(t, e.get, requestContext).map(_ => Seq()).recover {
            case e: BaseFidesException => e.errors
            case e: Throwable          => Seq(e.getMessage)
          }
        )
    )

}
