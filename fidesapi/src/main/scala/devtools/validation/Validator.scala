package devtools.validation

import com.typesafe.scalalogging.LazyLogging
import devtools.controller.RequestContext
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import scala.concurrent.Future
trait Validator[T, PK] extends LazyLogging {

  /** Perform any validations on the input object and collect any errors found.
    * Collect all errors found and return inside a ValidationException
    */
  def validateForCreate(t: T, ctx: RequestContext): Future[Unit]

  /** Allow for separate validation logic for updates */
  def validateForUpdate(t: T, existingValue: T, ctx: RequestContext): Future[Unit] = validateForCreate(t, ctx)

  /** Allow for separarte validation logic for deletions. */
  def validateForDelete(pk: PK, existingValue: T, ctx: RequestContext): Future[Unit] = Future.unit

  def validateFidesKey(fidesKey: String, errors: MessageCollector): MessageCollector = {
    if (sanitizeUniqueIdentifier(fidesKey) != fidesKey) {
      errors.addError(s"'$fidesKey' is not a valid identifier.")
    }
    errors
  }
}

object Validator {

  def noOp[T, PK]: Validator[T, PK] =
    new Validator[T, PK] {
      override def validateForCreate(t: T, ctx: RequestContext): Future[Unit] = Future.unit

      /** Allow for separate validation logic for updates */
      override def validateForUpdate(t: T, existingValue: T, ctx: RequestContext): Future[Unit] = Future.unit

      override def validateForDelete(pk: PK, existingValue: T, ctx: RequestContext): Future[Unit] =
        Future.unit

    }

}
