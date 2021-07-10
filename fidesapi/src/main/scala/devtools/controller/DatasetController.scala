package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.Dataset
import devtools.persist.dao.UserDAO
import devtools.persist.service.DatasetService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.scalate.ScalateSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DatasetController(val service: DatasetService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[Dataset, Long] with LongPK[Dataset] with ScalateSupport with GetByUniqueKey[Dataset] {
  val yamlFormat: YamlFormat[Dataset] = FidesYamlProtocols.DatasetFormat

}
