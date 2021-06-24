package devtools.persist.dao

import devtools.domain.{DataCategory, DataCategoryTree}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Queries.dataCategoryQuery
import devtools.persist.db.Tables.DataCategoryQuery
import devtools.util.TreeCache
import slick.dbio.{Effect, NoStream}
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._
import slick.lifted.Rep
import slick.sql.SqlStreamingAction

import scala.concurrent.{ExecutionContext, Future}
import scala.util.Success

class DataCategoryDAO(val db: Database)(implicit
  val executionContext: ExecutionContext
) extends DAO[DataCategory, Long, DataCategoryQuery](dataCategoryQuery)
  with AutoIncrementing[DataCategory, DataCategoryQuery] with ByOrganizationDAO[DataCategory, DataCategoryQuery]
  with TreeCache[DataCategoryTree, DataCategory] {

  cacheBuildAll()

  override def create(record: DataCategory): Future[DataCategory] = {
    super.create(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def update(record: DataCategory): Future[Option[DataCategory]] = {
    super.update(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def delete(id: Long): Future[Int] =
    for {
      r <- super.findById(id)
      i <- super.delete(id)
      _ = r.foreach(d => cacheBuild(d.organizationId))
    } yield i

  //TODO remove - this is only in use in tests
  def categoryReferencesCtAction(
    categoryName: String
  ): SqlStreamingAction[Vector[Long], Long, Effect]#ResultAction[Long, NoStream, Effect] = {
    sql"""select COUNT(*) FROM SYSTEM_OBJECT WHERE JSON_SEARCH(declarations, 'one','#$categoryName',NULL, '$$[*].dataCategories' ) IS NOT NULL"""
      .as[Long]
      .head
  }
  override implicit def getResult: GetResult[DataCategory] =
    r => DataCategory(r.<<[Long], r.<<?[Long], r.<<[Long], r.<<[String], r.<<?[String], r.<<?[String], r.<<?[String])

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): DataCategoryQuery => Rep[Option[Boolean]] = {
    t: DataCategoryQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value) ||
      (t.clause like value)
  }

}
