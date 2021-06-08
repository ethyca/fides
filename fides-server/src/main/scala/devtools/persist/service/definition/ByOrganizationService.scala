package devtools.persist.service.definition

import devtools.controller.RequestContext
import devtools.domain.definition.{IdType, OrganizationId}
import devtools.persist.dao.definition.{ByOrganization, DAO}
import devtools.persist.db.{BaseAutoIncTable, OrganizationIdTable}
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

abstract class ByOrganizationService[E <: IdType[E, Long] with OrganizationId](
  dao: DAO[E, Long, _ <: BaseAutoIncTable[E] with OrganizationIdTable[E]] with ByOrganization[E, _],
  validator: Validator[E, Long]
)(implicit ec: ExecutionContext)
  extends Service[E, Long](dao, validator) {
  override def getAll(ctx: RequestContext): Future[Seq[E]] = dao.findAllInOrganization(ctx.organizationId.getOrElse(-1))

  override def findById(id: Long, ctx: RequestContext): Future[Option[E]] =
    dao.findFirst(r => r.id === id && r.organizationId === ctx.organizationId).flatMap {
      case None    => Future.successful(None)
      case Some(e) => hydrate(e).map(x => Some(x))
    }

  override def search(value: String, ctx: RequestContext): Future[Seq[E]] =
    dao.searchInOrganization(ctx.organizationId.getOrElse(-1), value)
}
