package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.DatasetTable
import devtools.persist.dao.UserDAO
import devtools.persist.service.DatasetTableService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.scalate.ScalateSupport
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DatasetTableController(val service: DatasetTableService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[DatasetTable, Long] with LongPK[DatasetTable] with ScalateSupport
  with GetByUniqueKey[DatasetTable] {
  val yamlFormat: YamlFormat[DatasetTable] = FidesYamlProtocols.DatasetTableFormat

}
