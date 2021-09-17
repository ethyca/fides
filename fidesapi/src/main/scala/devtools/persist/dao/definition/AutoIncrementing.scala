package devtools.persist.dao.definition

import devtools.domain.definition.IdType
import devtools.persist.db.BaseAutoIncTable
import slick.dbio.Effect
import slick.jdbc.PostgresProfile.api._
import slick.sql.FixedSqlAction

/** Support for tables with a primary key that auto increments.
  * In practice all tables are currently defined this way.
  */
trait AutoIncrementing[E <: IdType[E, Long], T <: BaseAutoIncTable[E]] {
  val db: Database
  val query: slick.lifted.TableQuery[T]

  val insertQuery = query returning query.map(_.id) into ((item, id) => item.withId(id))

  def createAction(record: E): FixedSqlAction[E, NoStream, Effect.Write] = insertQuery += record.withId(0)

  def withId(record: E, id: Int): E = record.withId(id)
}
