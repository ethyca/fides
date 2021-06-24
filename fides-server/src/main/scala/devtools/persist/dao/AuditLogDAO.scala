package devtools.persist.dao

import devtools.domain.AuditLog
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganization, DAO}
import devtools.persist.db.Queries.auditLogQuery
import devtools.persist.db.Tables.AuditLogQuery
import slick.jdbc.MySQLProfile.api._
import slick.jdbc.{GetResult, MySQLProfile}

import scala.concurrent.{ExecutionContext, Future}

class AuditLogDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[AuditLog, Long, AuditLogQuery](auditLogQuery) with AutoIncrementing[AuditLog, AuditLogQuery]
  with ByOrganization[AuditLog, AuditLogQuery] {

  override def update(record: AuditLog): Future[Option[AuditLog]] =
    Future.failed(new UnsupportedOperationException("Updating of audit log records is not supported"))

  override def delete(id: Long): Future[Int] =
    Future.failed(new UnsupportedOperationException("deleting of audit log records is not supported"))

  override implicit def getResult: GetResult[AuditLog] =
    r =>
      AuditLog.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[Long],
        r.<<?[Long],
        r.<<[Long],
        r.<<[String],
        r.<<[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[java.sql.Timestamp]
      )

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: MySQLProfile.api.Rep[_]](
    value: String
  ): AuditLogQuery => MySQLProfile.api.Rep[Option[Boolean]] = { t: AuditLogQuery =>
    (t.typeName.toUpperCase like value) || (t.action like value) || (t.change like value)

  }
}
