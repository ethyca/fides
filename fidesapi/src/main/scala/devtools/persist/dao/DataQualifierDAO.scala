package devtools.persist.dao

import devtools.domain.{DataQualifier, DataQualifierTree}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.dataQualifierQuery
import devtools.persist.db.Tables.DataQualifierQuery
import devtools.util.TreeCache
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}
import scala.util.Success

/** Even though data qualifiers are strings, the values in ISO-19944 express a nested set
  * (identified(psuedonymized (unlinked_psuedonymized(anonymized (aggregated)))))
  * so it will be simpler to treat it as a (degenerate) tree.
  */
class DataQualifierDAO(val db: Database)(implicit
  val executionContext: ExecutionContext
) extends DAO[DataQualifier, Long, DataQualifierQuery](dataQualifierQuery)
  with AutoIncrementing[DataQualifier, DataQualifierQuery] with TreeCache[DataQualifierTree, DataQualifier]
  with ByOrganizationDAO[DataQualifier, DataQualifierQuery] {
  cacheBuildAll()

  override def create(record: DataQualifier): Future[DataQualifier] = {
    super.create(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def update(record: DataQualifier): Future[Option[DataQualifier]] = {
    super.update(record).andThen { case Success(_) => cacheBuild(record.organizationId) }
  }

  override def delete(id: Long): Future[Int] =
    for {
      r <- super.findById(id)
      i <- super.delete(id)
      _ = r.foreach(d => cacheBuild(d.organizationId))
    } yield i

  override implicit def getResult: GetResult[DataQualifier] =
    r => DataQualifier(r.<<[Long], r.<<?[Long], r.<<[Long], r.<<[String], r.<<?[String], r.<<?[String], r.<<?[String])

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): DataQualifierQuery => Rep[Option[Boolean]] = {
    t: DataQualifierQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value) ||
      (t.clause like value)
  }

}
