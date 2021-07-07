package devtools.persist.service

import devtools.domain.User
import devtools.persist.dao.UserDAO
import devtools.persist.db.Tables.UserQuery
import devtools.persist.service.definition.{ByOrganizationService, UniqueKeySearch}
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext

class UserService(dao: UserDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[User, UserQuery](dao, Validator.noOp[User, Long])(context)
  with UniqueKeySearch[User, UserQuery] {

  def findByUniqueKeyQuery(organizationId: Long, key: String): UserQuery => Rep[Boolean] = { q =>
    q.userName === key && q.organizationId === organizationId
  }

}
