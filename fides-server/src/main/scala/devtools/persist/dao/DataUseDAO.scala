package devtools.persist.dao

import devtools.domain.{DataUse, DataUseTree}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{DataUseQuery, dataUseQuery}
import devtools.util.TreeCache
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}
import scala.util.Success
class DataUseDAO(val db: Database)(implicit
  val executionContext: ExecutionContext
) extends DAO[DataUse, Long, DataUseQuery](dataUseQuery) with AutoIncrementing[DataUse, DataUseQuery]
  with ByOrganizationDAO[DataUse, DataUseQuery] with TreeCache[DataUseTree, DataUse] {

  cacheBuildAll()

  //TODO if you insert 0 parent id, sets to same as id
  override def create(record: DataUse): Future[DataUse] = {
    super.create(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def update(record: DataUse): Future[Option[DataUse]] = {
    super.update(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def delete(id: Long): Future[Int] =
    for {
      r <- super.findById(id)
      i <- super.delete(id)
      _ = r.foreach(d => cacheBuild(d.organizationId))
    } yield i

  override implicit def getResult: GetResult[DataUse] =
    r => DataUse(r.<<[Long], r.<<?[Long], r.<<[Long], r.<<[String], r.<<?[String], r.<<?[String], r.<<?[String])

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): DataUseQuery => Rep[Option[Boolean]] = {
    t: DataUseQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value) ||
      (t.clause like value)
  }

}
