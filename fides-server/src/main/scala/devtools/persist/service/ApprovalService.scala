package devtools.persist.service

import devtools.domain.Approval
import devtools.persist.dao.ApprovalDAO
import devtools.persist.db.Tables.ApprovalQuery
import devtools.persist.service.definition.ByOrganizationService
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class ApprovalService(dao: ApprovalDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[Approval, ApprovalQuery](dao, Validator.noOp[Approval, Long])(context) {

  def mostRecentSystem(id: Long): Future[Option[Approval]]   = dao.mostRecent(_.systemId === id)
  def mostRecentRegistry(id: Long): Future[Option[Approval]] = dao.mostRecent(_.registryId === id)
}
