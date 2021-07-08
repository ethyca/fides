package devtools.persist.service.definition

import devtools.domain.definition.IdType
import devtools.persist.db.BaseTable
import slick.lifted.{CanBeQueryCondition, Rep}

import scala.concurrent.Future
/** Support for searching by a unique key string, typically (but not exclusively)
  * a fidesKey memeber.
  */
trait UniqueKeySearch[E <: IdType[E, Long], T <: BaseTable[E, Long]] { self: Service[E, Long, T] =>

  /** query that will return a unique value. */
  def findByUniqueKeyQuery(organizationId: Long, key: String): (T => Rep[Boolean])

  /** return the unique value, hydrated if it is a compound object. */
  def findByUniqueKey(organizationId: Long, key: String): Future[Option[E]] = {
    val v    = findByUniqueKeyQuery(organizationId, key)
    val base = dao.findFirst(v)
    base.flatMap {
      case None    => Future.successful(None)
      case Some(r) => hydrate(r).map(Some(_))(ec)
    }
  }
}
