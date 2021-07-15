package devtools.persist.dao

import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{DatasetQuery, datasetFieldQuery, datasetQuery}
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

  /** retrieved all systems populated with fields */
  def findHydrated[C <: Rep[_]](
    expr: DatasetQuery => C
  )(implicit wt: CanBeQueryCondition[C]): Future[Iterable[Dataset]] = {
    val q = for {
      (s, d) <- query.filter(expr) joinLeft datasetFieldQuery on (_.id === _.datasetId)
    } yield (s, d)

    db.run(q.result).map { pairs =>
      pairs.groupBy(t => t._1.id).values.map { s: Seq[(Dataset, Option[DatasetField])] =>
        s.head._1.copy(fields = Some(s.map(_._2).filter(_.isDefined).map(_.get)))
      }
    }
  }
}
