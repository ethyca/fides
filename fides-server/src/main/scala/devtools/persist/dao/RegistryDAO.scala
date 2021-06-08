package devtools.persist.dao

import devtools.domain.{Registry, SystemObject}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganization, DAO}
import devtools.persist.db.Queries.{registryQuery, systemQuery}
import devtools.persist.db.Tables.RegistryQuery
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._
import slick.lifted.CanBeQueryCondition

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}

class RegistryDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[Registry, Long, RegistryQuery](registryQuery) with AutoIncrementing[Registry, RegistryQuery]
  with ByOrganization[Registry, RegistryQuery] {

  override implicit def getResult: GetResult[Registry] =
    r =>
      Registry(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[Long],
        r.<<?[String],
        r.<<?[String],
        None,
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): RegistryQuery => Rep[Option[Boolean]] = {
    t: RegistryQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value)
  }

  def setVersion(id: Long, version: Long): Future[Int] =
    db.run(query.filter(_.id === id).map(_.versionStamp).update(Some(version)))

  /** retrieved all policies with populated systems that match the given filter */
  def findHydrated[C <: Rep[_]](
    expr: RegistryQuery => C
  )(implicit wt: CanBeQueryCondition[C]): Future[Iterable[Registry]] = {
    val q = for {
      (reg, sys) <- query.filter(expr) join systemQuery on (_.id === _.registryId)
    } yield (reg, sys)

    db.run(q.result).map { pairs =>
      pairs.groupBy(t => t._2.registryId).values.map { s: Seq[(Registry, SystemObject)] =>
        s.head._1.copy(systems = Some(Right(s.map(_._2))))
      }
    }
  }

}
