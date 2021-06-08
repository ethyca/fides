package devtools.persist.service

import devtools.domain.User
import devtools.persist.dao.UserDAO
import devtools.persist.service.definition.{ByOrganizationService, UniqueKeySearch}
import devtools.validation.Validator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class UserService(dao: UserDAO)(implicit val context: ExecutionContext)
  extends ByOrganizationService[User](dao, Validator.noOp[User, Long])(context) with UniqueKeySearch[User] {

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[User]] =
    dao.findFirst(t => t.userName === key && t.organizationId === organizationId)

}
