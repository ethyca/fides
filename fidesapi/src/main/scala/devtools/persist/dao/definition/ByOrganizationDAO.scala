package devtools.persist.dao.definition

import devtools.domain.definition.{IdType, OrganizationId}
import devtools.persist.db.{BaseTable, OrganizationIdTable}
import devtools.util.Pagination
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.Future

trait ByOrganizationDAO[E <: IdType[E, Long] with OrganizationId, T <: BaseTable[E, Long] with OrganizationIdTable[E]] {
  this: DAO[E, Long, T] =>

  def findAllInOrganization(organizationId: Long, pagination: Pagination): Future[Seq[E]] =
    filterPaginated(_.organizationId === organizationId, _.id, pagination)

  /** Search clause by string fields to be defined by type. */
  def searchInOrganizationAction[C <: Rep[_]](value: String): T => Rep[Option[Boolean]]

  /** Paginated search within an organization. */
  def searchInOrganization(organizationId: Long, value: String, pagination: Pagination): Future[Seq[E]] = {
    val searchValue = s"%${value.toUpperCase()}%"

    db.run(
      query
        .filter(_.organizationId === organizationId)
        .filter(searchInOrganizationAction(searchValue))
        .sorted(_.id)
        .drop(pagination.offset)
        .take(pagination.limit)
        .result
    )
  }
}
