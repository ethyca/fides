package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.Dataset
import devtools.persist.dao.DAOs

import scala.concurrent.{ExecutionContext, Future}

class DatasetValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[Dataset, Long] with ValidateByOrganization {

  /** Validations:
    *
    * - referenced organization exists.
    */
  def validateForCreate(t: Dataset, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    validateFidesKey(t.fidesKey, errors)
    requireOrganizationIdExists(t.organizationId, errors).flatMap(_.asFuture())
  }
  /** if fideskey changes, validate that it's not in use.
    */
  override def validateForUpdate(t: Dataset, previous: Dataset, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    validateFidesKey(t.fidesKey, errors)
    for {
      _ <- {
        if (previous.organizationId != t.organizationId) {
          requireOrganizationIdExists(t.organizationId, errors)
        } else {
          Future.successful(errors)
        }
      }
      _ <- {
        if (previous.fidesKey != t.fidesKey) {
          checkFidesKeyInUse(previous.organizationId, previous.fidesKey, errors)
        } else {
          Future.successful(errors)
        }
      }
      e <- errors.asFuture()
    } yield e
  }

  /** A dataset fides key name has the additional constraint that it cannot contain a '.'
    * to disambiguate field references in "table.field" syntax
    */
  def validateFidesKey(s: String, errors: MessageCollector) =
    if (s.contains('.')) { errors.addError("Dataset fides keys can not contain a '.'") }

  /** if fides key is in use, fail.
    */
  override def validateForDelete(pk: Long, existing: Dataset, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    checkFidesKeyInUse(existing.organizationId, existing.fidesKey, errors).flatMap(_.asFuture())
  }

  def checkFidesKeyInUse(organizationId: Long, fidesKey: String, errors: MessageCollector): Future[MessageCollector] = {
    daos.privacyDeclarationDAO
      .systemsReferencingDataset(organizationId, fidesKey)
      .map(keys => {
        if (keys.nonEmpty) {
          errors.addError(s"The systems ${keys.mkString(",")} are using dataset $fidesKey")
        }

        errors
      })
  }
}
