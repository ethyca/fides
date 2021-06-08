package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK, TreeDisplay}
import devtools.domain.{DataUse, DataUseTree}
import devtools.persist.dao.UserDAO
import devtools.persist.service.DataUseService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DataUseController(val service: DataUseService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[DataUse, Long] with LongPK[DataUse] with TreeDisplay[DataUse, Long, DataUseTree]
  with GetByUniqueKey[DataUse] {

  val yamlFormat: YamlFormat[DataUse] = FidesYamlProtocols.DataUseFormat

  override def taxonomyGetAll(): Iterable[DataUseTree] =
    service.dao.cacheGetRoots(requestContext.organizationId.getOrElse(-1))

  override def taxonomyGetById(id: Long): Option[DataUseTree] =
    service.dao.cacheGet(requestContext.organizationId.getOrElse(-1), id)
}
