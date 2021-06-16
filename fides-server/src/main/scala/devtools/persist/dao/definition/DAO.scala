package devtools.persist.dao.definition

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.definition.IdType
import devtools.persist.db.BaseTable
import slick.dbio.{DBIOAction, Effect, NoStream}
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._
import slick.lifted.CanBeQueryCondition
import slick.sql.FixedSqlAction

import scala.concurrent.{ExecutionContext, Future}

/** Base class for accessors that connect directly to the database. CRUD operations map
  * to simple DB CRUD operations
  */
abstract class DAO[E <: IdType[E, PK], PK: BaseColumnType, T <: BaseTable[E, PK]](
  val query: slick.lifted.TableQuery[T]
) extends LazyLogging {

  implicit def executionContext: ExecutionContext
  implicit def getResult: GetResult[E]
  val db: Database

  def getAll: Future[Seq[E]] = db.run(query.result)

  def findById(id: PK): Future[Option[E]] = db.run(findByIdAction(id))

  def deleteAll(): Future[Int] =
    db.run(sqlu"""TRUNCATE TABLE "#${query.baseTableRow.tableName}" """)

  def filter[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Seq[E]] =
    db.run(query.filter(expr).result)

  def count[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Int] =
    db.run(query.filter(expr).length.result)

  def exists[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Boolean] =
    count(expr).map(_ > 0)

  def runAction[R](action: DBIOAction[R, NoStream, Nothing]): Future[R] = db.run(action)

  def findFirst[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Option[E]] =
    db.run(query.filter(expr).result.headOption)

  def create(record: E): Future[E] = db.run(createAction(record))

  def update(record: E): Future[Option[E]] = db.run(updateAction(record))

  def delete(id: PK): Future[Int] = db.run(deleteAction(id))

  def delete[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Int] =
    db.run(query.filter(expr).delete)

  def createAction(record: E): FixedSqlAction[E, NoStream, Effect.Write]

  def updateAction(
    record: E
  ): DBIOAction[Option[E], NoStream, Effect.Write with Effect.Read with Effect.Transactional] =
    query.filter(_.id === record.id).update(record).flatMap { _ => findByIdAction(record.id) }.transactionally

  def deleteAction(id: PK): DBIOAction[Int, NoStream, Effect.Write] = query.filter(_.id === id).delete

  def findByIdAction(id: PK): DBIOAction[Option[E], NoStream, Effect.Read] = query.filter(_.id === id).result.headOption

  /** find the most recent value matching expr, sorting by id column. */
  def mostRecent[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Option[E]] =
    db.run(query.filter(expr).sorted(_.id.desc).take(1).result.headOption)

}
