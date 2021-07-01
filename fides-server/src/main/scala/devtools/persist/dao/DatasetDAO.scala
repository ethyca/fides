package devtools.persist.dao

import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Queries.{datasetFieldQuery, datasetQuery}
import devtools.persist.db.Tables.DatasetQuery
import slick.jdbc.MySQLProfile.api._
import slick.jdbc.{GetResult, MySQLProfile}
import slick.lifted.CanBeQueryCondition

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}

class DatasetDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[Dataset, Long, DatasetQuery](datasetQuery) with AutoIncrementing[Dataset, DatasetQuery]
  with ByOrganizationDAO[Dataset, DatasetQuery] {

  override implicit def getResult: GetResult[Dataset] =
    r =>
      Dataset.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[Long],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: MySQLProfile.api.Rep[_]](
    value: String
  ): DatasetQuery => MySQLProfile.api.Rep[Option[Boolean]] = { t: DatasetQuery =>
    (t.fidesKey.toUpperCase like value) ||
    (t.fidesKey like value) ||
    (t.name like value) ||
    (t.description like value) ||
    (t.datasetType like value) ||
    (t.location like value)
  }

  /** Retrieve all datasets that match the given filter populated with fields. */
  def findHydrated[C <: Rep[_]](
    expr: DatasetQuery => C
  )(implicit wt: CanBeQueryCondition[C]): Future[Iterable[Dataset]] = {
    val q = for {
      (dataset, field) <- query.filter(
        expr
      ) join datasetFieldQuery on (_.id === _.datasetId)
    } yield (dataset, field)

    db.run(q.result).map { t =>
      t.groupBy(_._1).map { t1: (Dataset, Seq[(Dataset, DatasetField)]) =>
        t1._1.copy(fields = Some(t1._2.map(_._2)))
      }
    }
  }

}
