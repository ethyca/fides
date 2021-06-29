package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DatasetTable
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetTableValidator(daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DatasetTable, Long] {

  /** Validations:
    *
    * - parent table exists
    */
  def validateForCreate(t: DatasetTable, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    requireDatasetExists(t.datasetId, errors).flatMap { _ => errors.asFuture() }
  }

  /** The table this is attached to must exist. */
  def requireDatasetExists(datasetId: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.datasetDAO.exists(_.id === datasetId).map { exists: Boolean =>
      if (!exists) {
        errors.addError(s"The value '$datasetId' given as the datasetId does not exist.")
      }
      errors
    }
}
