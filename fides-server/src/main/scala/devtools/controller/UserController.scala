package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.User
import devtools.persist.dao.UserDAO
import devtools.persist.service.UserService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class UserController(val service: UserService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[User, Long] with LongPK[User] with GetByUniqueKey[User] {

  val yamlFormat: YamlFormat[User] = FidesYamlProtocols.UserFormat

}
