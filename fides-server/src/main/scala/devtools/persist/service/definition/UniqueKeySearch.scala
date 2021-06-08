package devtools.persist.service.definition

import devtools.domain.definition.IdType

import scala.concurrent.Future

trait UniqueKeySearch[E <: IdType[E, _]] {

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[E]]
}
