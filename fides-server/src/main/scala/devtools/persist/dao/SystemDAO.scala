package devtools.persist.dao

import devtools.domain.SystemObject
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{SystemQuery, systemQuery}
import slick.dbio.{Effect, NoStream}
import slick.jdbc.MySQLProfile.api._
import slick.jdbc.{GetResult, MySQLProfile}
import slick.lifted.CanBeQueryCondition
import slick.sql.FixedSqlAction

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}

class SystemDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[SystemObject, Long, SystemQuery](systemQuery) with AutoIncrementing[SystemObject, SystemQuery]
  with ByOrganizationDAO[SystemObject, SystemQuery] {
  override implicit def getResult: GetResult[SystemObject] =
    r =>
      SystemObject.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<?[Long],
        r.<<[String],
        r.<<?[Long],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )
  /** Unset the registry ids for any systems matching the given filter */
  def setRegistryIds[C <: Rep[_]](registryId: Long, expr: SystemQuery => C)(implicit
    wt: CanBeQueryCondition[C]
  ): Future[Int] =
    runAction(systemQuery.filter(expr).map(_.registryId).update(Some(registryId)))
  /** Unset the registry ids for any systems matching the given filter */
  def unsetRegistryIds[C <: Rep[_]](expr: SystemQuery => C)(implicit wt: CanBeQueryCondition[C]): Future[Int] =
    runAction(systemQuery.filter(expr).map(_.registryId).update(None))

  override def createAction(record: SystemObject): FixedSqlAction[SystemObject, NoStream, Effect.Write] =
    insertQuery += record.copy(id = 0, creationTime = None, lastUpdateTime = None)

  /* find id for unique name/organizationId pair.*/
  def findIdForNameAndOrg(name: String, organizationId: Long): Future[Option[Long]] = {
    db.run(
      query
        .filter(sys => { sys.name === name && sys.organizationId === organizationId })
        .map(s => s.id)
        .result
        .headOption
    )
  }

  def findForFidesKeyInSet(fidesKeys: Set[String], organizationId: Long): Future[Seq[SystemObject]] =
    db.run(systemQuery.filter(sys => { sys.fidesKey.inSet(fidesKeys) && sys.organizationId === organizationId }).result)

  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: MySQLProfile.api.Rep[_]](
    value: String
  ): SystemQuery => MySQLProfile.api.Rep[Option[Boolean]] = { t: SystemQuery =>
    (t.fidesKey.toUpperCase like value) ||
    (t.systemType like value) ||
    (t.name like value) ||
    (t.description like value) ||
    (t.systemDependencies like value)
  }

}
