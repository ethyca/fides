package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.Organization
import devtools.persist.dao.UserDAO
import devtools.persist.service.OrganizationService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class OrganizationController(val service: OrganizationService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[Organization, Long] with LongPK[Organization] with GetByUniqueKey[Organization] {

  val yamlFormat: YamlFormat[Organization] = FidesYamlProtocols.OrganizationFormat

}
