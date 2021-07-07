package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.DatasetField
import devtools.persist.dao.UserDAO
import devtools.persist.service.DatasetFieldService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.scalate.ScalateSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DatasetFieldController(val service: DatasetFieldService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[DatasetField, Long] with LongPK[DatasetField] with ScalateSupport {
  val yamlFormat: YamlFormat[DatasetField] = FidesYamlProtocols.DatasetFieldFormat

}
