package devtools.validation

import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

trait ValidateByOrganization {

  val daos: DAOs
  implicit val executionContext: ExecutionContext

  /** Validate that the referenced organization exists. */
  def requireOrganizationIdExists(organizationId: Long, errors: MessageCollector): Future[MessageCollector] =
    daos.organizationDAO.exists(_.id === organizationId).map { exists: Boolean =>
      if (!exists) {
        errors.addError(s"The value '$organizationId' given as the organizationId does not exist.")
      }
      errors
    }
}
