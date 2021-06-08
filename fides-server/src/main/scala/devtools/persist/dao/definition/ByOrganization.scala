package devtools.persist.dao.definition

import devtools.domain.definition.{IdType, OrganizationId}
import devtools.persist.db.{BaseTable, OrganizationIdTable}
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.Future

trait ByOrganization[E <: IdType[E, Long] with OrganizationId, T <: BaseTable[E, Long] with OrganizationIdTable[E]] {
  this: DAO[E, Long, T] =>

  def findAllInOrganization(organizationId: Long): Future[Seq[E]] =
    db.run(query.filter(_.organizationId === organizationId).result)

  /** Search clause by string fields */
  def searchInOrganizationAction[C <: Rep[_]](value: String): T => Rep[Option[Boolean]]

  def searchInOrganization(organizationId: Long, value: String): Future[Seq[E]] = {
    val searchValue = s"%${value.toUpperCase()}%"
    db.run(query.filter(_.organizationId === organizationId).filter(searchInOrganizationAction(searchValue)).result)
  }
}
