package devtools.persist.dao

import devtools.domain.{DataSubject, DataSubjectTree}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{DataSubjectQuery, dataSubjectQuery}
import devtools.util.TreeCache
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}
import scala.util.Success

class DataSubjectDAO(val db: Database)(implicit
  val executionContext: ExecutionContext
) extends DAO[DataSubject, Long, DataSubjectQuery](dataSubjectQuery)
  with AutoIncrementing[DataSubject, DataSubjectQuery] with ByOrganizationDAO[DataSubject, DataSubjectQuery]
  with TreeCache[DataSubjectTree, DataSubject] {

  cacheBuildAll()

  override def create(record: DataSubject): Future[DataSubject] = {
    super.create(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def update(record: DataSubject): Future[Option[DataSubject]] = {
    super.update(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def delete(id: Long): Future[Int] =
    for {
      r <- super.findById(id)
      i <- super.delete(id)
      _ = r.foreach(d => cacheBuild(d.organizationId))
    } yield i

  override implicit def getResult: GetResult[DataSubject] =
    r => DataSubject(r.<<[Long], r.<<?[Long], r.<<[Long], r.<<[String], r.<<?[String], r.<<?[String])

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](
    value: String
  ): DataSubjectQuery => Rep[Option[Boolean]] = { t: DataSubjectQuery =>
    (t.fidesKey like value) ||
    (t.name like value) ||
    (t.parentKey like value) ||
    (t.description like value)
  }
}
