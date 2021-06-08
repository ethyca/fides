package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK, TreeDisplay}
import devtools.domain.{DataCategory, DataCategoryTree}
import devtools.persist.dao.UserDAO
import devtools.persist.service.DataCategoryService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DataCategoryController(val service: DataCategoryService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[DataCategory, Long] with LongPK[DataCategory]
  with TreeDisplay[DataCategory, Long, DataCategoryTree] with GetByUniqueKey[DataCategory] {

  val yamlFormat: YamlFormat[DataCategory] = FidesYamlProtocols.DataCategoryFormat

  override def taxonomyGetAll(): Iterable[DataCategoryTree] =
    service.dao.cacheGetRoots(requestContext.organizationId.getOrElse(-1))

  override def taxonomyGetById(id: Long): Option[DataCategoryTree] =
    service.dao.cacheGet(requestContext.organizationId.getOrElse(-1), id)
}
