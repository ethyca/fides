package devtools.persist.service.definition

import devtools.controller.RequestContext
import devtools.domain.definition.IdType
import devtools.exceptions.NoSuchValueException
import devtools.persist.dao.definition.DAO
import devtools.persist.db.BaseTable
import devtools.util.Pagination
import devtools.validation.Validator

import scala.concurrent.{ExecutionContext, Future}

/** A service represents an interface for a type mapped to a db table.
  * A DAO only handles direct db CRUD operations without any application
  * logic.
  *
  * The service itself represents application logic wrapped around the DAO,
  * including
  * - limiting by organization where appropriate
  * - hydrating values that have One-to_many members
  * - validation logic
  */
abstract class Service[E <: IdType[E, PK], PK, T <: BaseTable[E, PK]](
  val dao: DAO[E, PK, T],
  validator: Validator[E, PK]
)(implicit
  val ec: ExecutionContext
) {
  def getAll(ctx: RequestContext, pagination: Pagination): Future[Seq[E]] = dao.getAll(pagination)

  /** return a (hydrated) value */
  def findById(id: PK, ctx: RequestContext): Future[Option[E]] =
    dao.findById(id).flatMap {
      case None    => Future.successful(None)
      case Some(e) => hydrate(e).map(x => Some(x))
    }

  /** Override this for returning hydrated values, for example in returning objects with composite 1-to-many or many-to-many members */
  def hydrate(e: E): Future[E] = Future.successful(e)

  def create(record: E, ctx: RequestContext): Future[E] =
    validator.validateForCreate(record, ctx).flatMap(_ => createValidated(record, ctx))

  def update(record: E, ctx: RequestContext): Future[Option[E]] =
    dao.findById(record.id).flatMap {
      case Some(e) => validator.validateForUpdate(record, e, ctx).flatMap(_ => updateValidated(record, e, ctx))
      case None    => Future.failed(NoSuchValueException("id", record.id))
    }

  def delete(id: PK, ctx: RequestContext): Future[Int] =
    dao.findById(id).flatMap {
      case Some(e) => validator.validateForDelete(id, e, ctx).flatMap(_ => deleteValidated(id, e, ctx))
      case None    => Future.failed(NoSuchValueException("id", id))
    }

  def createValidated(record: E, ctx: RequestContext): Future[E] = dao.create(record)

  def updateValidated(record: E, previous: E, ctx: RequestContext): Future[Option[E]] = dao.update(record)

  def deleteValidated(id: PK, previous: E, ctx: RequestContext): Future[Int] = dao.delete(id)

  def search(s: String, ctx: RequestContext, pagination: Pagination): Future[Seq[E]] =
    Future.failed(new UnsupportedOperationException("search is not yet supported for this type"))

}
