package devtools.persist.service.definition

import devtools.domain.definition.IdType

import scala.concurrent.Future
/** Support for searching by a unique key string, typically (but not exclusively)
  * a fidesKey memeber. */
trait UniqueKeySearch[E <: IdType[E, _]] {

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[E]]
}
