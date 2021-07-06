package devtools.persist.dao

import devtools.domain.SystemObject
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Queries.systemQuery
import devtools.persist.db.Tables.SystemQuery
import devtools.util.Sanitization.sanitizeUniqueIdentifier
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

  /** i.e  select id FROM SYSTEM_OBJECT WHERE JSON_SEARCH(privacy_declarations, 'one','telemetry_data',NULL, '$[*].dataCategories' ) IS NOT NULL; */
  def findSystemsWithJsonMember(organizationId: Long, fidesKey: String, memberName: String): Future[Seq[Long]] = {
    val typeKey   = s"$$[*].$memberName"
    val sanitized = sanitizeUniqueIdentifier(fidesKey)
    db.run(
      sql"""select id FROM SYSTEM_OBJECT WHERE organization_id = #$organizationId AND JSON_SEARCH(privacy_declarations, 'one','#$sanitized',NULL, '#$typeKey' ) IS NOT NULL"""
        .as[Long]
    )
  }

  /** find systems that reference a particular dataset. */
  def findSystemsWithDataset(organizationId: Long, fidesKey: String): Future[Seq[Long]] = {
    val sanitized = sanitizeUniqueIdentifier(fidesKey)
    db.run(
      sql""" select id FROM SYSTEM_OBJECT WHERE organization_id = #$organizationId AND JSON_SEARCH(privacy_declarations, 'one','#$sanitized',NULL, '$$[*].references' ) IS NOT NULL;"""
        .as[Long]
    )
  }

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
