package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK, TreeDisplay}
import devtools.domain.{DataSubjectCategory, DataSubjectCategoryTree}
import devtools.persist.dao.UserDAO
import devtools.persist.service.DataSubjectCategoryService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DataSubjectCategoryController(
  val service: DataSubjectCategoryService,
  val userDAO: UserDAO,
  val swagger: Swagger
)(implicit
  executor: ExecutionContext
) extends BaseController[DataSubjectCategory, Long] with LongPK[DataSubjectCategory]
  with TreeDisplay[DataSubjectCategory, Long, DataSubjectCategoryTree] with GetByUniqueKey[DataSubjectCategory] {

  val yamlFormat: YamlFormat[DataSubjectCategory] = FidesYamlProtocols.SubjectCategoryFormat

  override def taxonomyGetAll(): Iterable[DataSubjectCategoryTree] =
    service.dao.cacheGetRoots(requestContext.organizationId)

  override def taxonomyGetById(id: Long): Option[DataSubjectCategoryTree] =
    service.dao.cacheGet(requestContext.organizationId, id)
}
