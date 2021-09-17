package devtools.persist.service

import devtools.domain.Organization
import devtools.persist.dao.OrganizationDAO
import devtools.persist.db.Tables.OrganizationQuery
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.{OrganizationValidator, Validator}
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.ExecutionContext

class OrganizationService(dao: OrganizationDAO)(implicit val context: ExecutionContext)
  extends Service[Organization, Long, OrganizationQuery](dao, new OrganizationValidator)(context)
  with UniqueKeySearch[Organization, OrganizationQuery] {

  /** Note - Since the organization id is redunant and already returns a unique value this implementation ignores the
    * organization id but can support a more general search.
    */
  def findByUniqueKeyQuery(organizationId: Long, key: String): OrganizationQuery => Rep[Boolean] = _.fidesKey === key
}
