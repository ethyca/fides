package devtools.persist.dao

import devtools.domain.{DataSubjectCategory, DataSubjectCategoryTree}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Queries.dataSubjectCategoryQuery
import devtools.persist.db.Tables.DataSubjectCategoryQuery
import devtools.util.TreeCache
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}
import scala.util.Success

class DataSubjectCategoryDAO(val db: Database)(implicit
  val executionContext: ExecutionContext
) extends DAO[DataSubjectCategory, Long, DataSubjectCategoryQuery](dataSubjectCategoryQuery)
  with AutoIncrementing[DataSubjectCategory, DataSubjectCategoryQuery]
  with ByOrganizationDAO[DataSubjectCategory, DataSubjectCategoryQuery]
  with TreeCache[DataSubjectCategoryTree, DataSubjectCategory] {

  cacheBuildAll()

  override def create(record: DataSubjectCategory): Future[DataSubjectCategory] = {
    super.create(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def update(record: DataSubjectCategory): Future[Option[DataSubjectCategory]] = {
    super.update(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def delete(id: Long): Future[Int] =
    for {
      r <- super.findById(id)
      i <- super.delete(id)
      _ = r.foreach(d => cacheBuild(d.organizationId))
    } yield i

  override implicit def getResult: GetResult[DataSubjectCategory] =
    r => DataSubjectCategory(r.<<[Long], r.<<?[Long], r.<<[Long], r.<<[String], r.<<?[String], r.<<?[String])

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](
    value: String
  ): DataSubjectCategoryQuery => Rep[Option[Boolean]] = { t: DataSubjectCategoryQuery =>
    (t.fidesKey like value) ||
    (t.name like value) ||
    (t.description like value)
  }
}
