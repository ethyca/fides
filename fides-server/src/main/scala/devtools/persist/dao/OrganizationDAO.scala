package devtools.persist.dao

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.{DataCategory, DatasetField, Organization}
import devtools.persist.dao.definition.{AutoIncrementing, DAO}
import devtools.persist.db.Queries.organizationQuery
import devtools.persist.db.Tables.OrganizationQuery
import slick.dbio.{Effect, NoStream}
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._
import slick.sql.{FixedSqlAction, SqlAction}

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}

class OrganizationDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[Organization, Long, OrganizationQuery](organizationQuery)
  with AutoIncrementing[Organization, OrganizationQuery] with LazyLogging {
  override implicit def getResult: GetResult[Organization] =
    r =>
      Organization(
        r.<<[Long],
        r.<<[String],
        r.<<?[Long],
        r.<<?[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )

  override def createAction(record: Organization): FixedSqlAction[Organization, NoStream, Effect.Write] =
    insertQuery += record.copy(id = 0, creationTime = None, lastUpdateTime = None)

  def getAndIncrementVersionAction(id: Long): DBIOAction[Option[Long], NoStream, Effect with Effect.Read] = {
    for {
      _ <-
        sql"""UPDATE ORGANIZATION SET VERSION_STAMP = VERSION_STAMP + 1,  LAST_UPDATE_TIME = CURRENT_TIMESTAMP WHERE ID = $id"""
          .as[Long]
      version: Option[Option[Long]] <- query.filter(_.id === id).map(_.versionStamp).result.headOption
    } yield version match {
      case Some(Some(l)) => Some(l)
      case _             => None
    }
  }

  def getAndIncrementVersion(id: Long): Future[Long] =
    db.run(getAndIncrementVersionAction(id).transactionally).flatMap {
      case Some(l) => Future.successful(l)
      case None    => Future.failed(new Exception(s"Error incrementing org counter for id $id"))
    }

  def getVersion(id: Long): Future[Option[Long]] =
    db.run(query.filter(_.id === id).map(_.versionStamp).result.headOption)
      .map({
        case Some(Some(s)) => Some(s)
        case _             => None
      })

}
