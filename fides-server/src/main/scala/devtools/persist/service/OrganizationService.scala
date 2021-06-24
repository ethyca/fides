package devtools.persist.service

import devtools.domain.Organization
import devtools.persist.dao.OrganizationDAO
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import slick.jdbc.MySQLProfile.api._
import devtools.validation.Validator

import scala.concurrent.{ExecutionContext, Future}

class OrganizationService(dao: OrganizationDAO)(implicit val context: ExecutionContext)
  extends Service[Organization, Long](dao, Validator.noOp[Organization, Long])(context)
  with UniqueKeySearch[Organization] {

  /** Note - Since the organization id is redunant and already returns a unique value this implementation ignores the
    * organization id but can support a more general search.
    */
  def findByUniqueKey(organizationId: Long, key: String): Future[Option[Organization]] =
    dao.findFirst(_.fidesKey === key)
}
