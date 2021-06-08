package devtools.persist.dao

import devtools.domain.Approval
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganization, DAO}
import devtools.persist.db.Queries.approvalQuery
import devtools.persist.db.Tables.ApprovalQuery
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext

class ApprovalDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[Approval, Long, ApprovalQuery](approvalQuery) with ByOrganization[Approval, ApprovalQuery]
  with AutoIncrementing[Approval, ApprovalQuery] {
  implicit def getResult: GetResult[Approval] =
    r =>
      Approval.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<?[Long],
        r.<<?[Long],
        r.<<[Long],
        r.<<?[Long],
        r.<<[String],
        r.<<[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[java.sql.Timestamp]
      )

  def searchInOrganizationAction[C <: Rep[_]](value: String): ApprovalQuery => Rep[Option[Boolean]] = {
    t: ApprovalQuery => (t.status like value) || (t.details like value) || (t.messages like value)
  }

}
