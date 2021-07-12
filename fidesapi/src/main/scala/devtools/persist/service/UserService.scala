package devtools.persist.service

import devtools.controller.RequestContext
import devtools.domain.User
import devtools.persist.dao.UserDAO
import devtools.persist.db.Tables.UserQuery
import devtools.persist.service.definition.{ByOrganizationService, UniqueKeySearch}
import devtools.util.JwtUtil
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class UserService(dao: UserDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[User, UserQuery](dao, Validator.noOp[User, Long])(context)
  with UniqueKeySearch[User, UserQuery] {


  /** Generate an api key*/
override def create(user:User, ctx: RequestContext): Future[User] = super.create(user.copy(apiKey = JwtUtil.generateToken()),ctx)

  def findByUniqueKeyQuery(organizationId: Long, key: String): UserQuery => Rep[Boolean] = { q =>
    q.userName === key && q.organizationId === organizationId
  }

}
