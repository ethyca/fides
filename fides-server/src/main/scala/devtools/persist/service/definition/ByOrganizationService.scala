package devtools.persist.service.definition

import devtools.controller.RequestContext
import devtools.domain.definition.{IdType, OrganizationId}
import devtools.persist.dao.definition.{ByOrganizationDAO, DAO}
import devtools.persist.db.{BaseAutoIncTable, BaseTable, OrganizationIdTable}
import devtools.util.Pagination
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** Extension of Service for objects that are segmented by organization id. */
abstract class ByOrganizationService[E <: IdType[E, Long] with OrganizationId, T <: BaseAutoIncTable[
  E
] with OrganizationIdTable[E]](
  dao: DAO[E, Long, T] with ByOrganizationDAO[E, _],
  validator: Validator[E, Long]
)(implicit ec: ExecutionContext)
  extends Service[E, Long, T](dao, validator) {
  override def getAll(ctx: RequestContext, pagination: Pagination): Future[Seq[E]] =
    dao.findAllInOrganization(ctx.organizationId, pagination)

  override def findById(id: Long, ctx: RequestContext): Future[Option[E]] =
    dao.findFirst(r => r.id === id && r.organizationId === ctx.organizationId).flatMap {
      case None    => Future.successful(None)
      case Some(e) => hydrate(e).map(x => Some(x))
    }

  override def search(value: String, ctx: RequestContext, pagination: Pagination): Future[Seq[E]] =
    dao.searchInOrganization(ctx.organizationId, value, pagination)
}
