package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK, TreeDisplay}
import devtools.domain.{DataQualifier, DataQualifierTree}
import devtools.persist.dao.UserDAO
import devtools.persist.service.DataQualifierService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DataQualifierController(val service: DataQualifierService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[DataQualifier, Long] with LongPK[DataQualifier]
  with TreeDisplay[DataQualifier, Long, DataQualifierTree] with GetByUniqueKey[DataQualifier] {

  val yamlFormat: YamlFormat[DataQualifier] = FidesYamlProtocols.DataQualifierFormat

  override def taxonomyGetAll(): Iterable[DataQualifierTree] =
    service.dao.cacheGetRoots(requestContext.organizationId)

  override def taxonomyGetById(id: Long): Option[DataQualifierTree] =
    service.dao.cacheGet(requestContext.organizationId, id)

}
