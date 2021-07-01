package devtools.controller

import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK, TreeDisplay}
import devtools.domain.{DataSubject, DataSubjectTree}
import devtools.persist.dao.UserDAO
import devtools.persist.service.DataSubjectService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext

class DataSubjectController(
  val service: DataSubjectService,
  val userDAO: UserDAO,
  val swagger: Swagger
)(implicit
  executor: ExecutionContext
) extends BaseController[DataSubject, Long] with LongPK[DataSubject]
  with TreeDisplay[DataSubject, Long, DataSubjectTree] with GetByUniqueKey[DataSubject] {

  val yamlFormat: YamlFormat[DataSubject] = FidesYamlProtocols.SubjectCategoryFormat

  override def taxonomyGetAll(): Iterable[DataSubjectTree] =
    service.dao.cacheGetRoots(requestContext.organizationId)

  override def taxonomyGetById(id: Long): Option[DataSubjectTree] =
    service.dao.cacheGet(requestContext.organizationId, id)
}
