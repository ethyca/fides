package devtools.persist.dao.definition

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.definition.IdType
import devtools.persist.db.BaseTable
import devtools.util.Pagination
import slick.dbio.{DBIOAction, Effect, NoStream}
import slick.jdbc.GetResult
import slick.jdbc.PostgresProfile.api._
import slick.lifted.{CanBeQueryCondition, Ordered}
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

  def count[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Int] =
    db.run(query.filter(expr).length.result)

  def exists[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Boolean] =
    count(expr).map(_ > 0)

  def runAction[R](action: DBIOAction[R, NoStream, Nothing]): Future[R] = db.run(action)

  def create(record: E): Future[E] = db.run(createAction(record))

  def update(record: E): Future[Option[E]] = db.run(updateAction(record))

  def delete(id: PK): Future[Int] = db.run(deleteAction(id))

  def delete[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Int] =
    db.run(query.filter(expr).delete)

  // ---------------------------
  // find
  // ---------------------------

  // pagination defaults
  val DEFAULT_SORT: T => Rep[PK]     = _.id
  val DEFAULT_PAGINATION: Pagination = Pagination()

  def getAll(pagination: Pagination): Future[Seq[E]] = getAllPaginated(DEFAULT_SORT, pagination)

  /** Support pagination values */
  def getAllPaginated[C <: Rep[_]](sort: T => C, pagination: Pagination)(implicit ev: C => Ordered): Future[Seq[E]] =
    db.run(query.sortBy(sort)(ev).drop(pagination.offset).take(pagination.limit).result)

  // by default we sort and return by id.
  def filter[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Seq[E]] =
    filterPaginated(expr, DEFAULT_SORT, DEFAULT_PAGINATION)

  /** Support pagination values */
  def filterPaginated[SRT <: Rep[_], ORD <: Rep[_]](expr: T => ORD, sort: T => SRT, pagination: Pagination)(implicit
    ev: SRT => Ordered,
    wt: CanBeQueryCondition[ORD]
  ): Future[Seq[E]] = db.run(query.filter(expr).sortBy(sort)(ev).drop(pagination.offset).take(pagination.limit).result)

  def findById(id: PK): Future[Option[E]] = db.run(findByIdAction(id))

  def findFirst[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Option[E]] =
    db.run(query.filter(expr).result.headOption)

  /** find the most recent value matching expr, sorting by id column. */
  def mostRecent[C <: Rep[_]](expr: T => C)(implicit wt: CanBeQueryCondition[C]): Future[Option[E]] =
    db.run(query.filter(expr).sorted(_.id.desc).take(1).result.headOption)

  // ------------------
  // actions
  // ------------------
  def createAction(record: E): FixedSqlAction[E, NoStream, Effect.Write]

  def updateAction(
    record: E
  ): DBIOAction[Option[E], NoStream, Effect.Write with Effect.Read with Effect.Transactional] =
    query.filter(_.id === record.id).update(record).flatMap { _ => findByIdAction(record.id) }.transactionally

  def deleteAction(id: PK): DBIOAction[Int, NoStream, Effect.Write] = query.filter(_.id === id).delete

  def findByIdAction(id: PK): DBIOAction[Option[E], NoStream, Effect.Read] = query.filter(_.id === id).result.headOption

}
