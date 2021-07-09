package devtools.controller

import devtools.controller.definition.ApiResponse.asyncResponse
import devtools.controller.definition.BaseController
import devtools.domain.AuditLog
import devtools.persist.dao.{AuditLogDAO, UserDAO}
import devtools.persist.db.Tables.auditLogQuery
import devtools.persist.service.AuditLogService
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext
import scala.util.Try
class AuditLogController(val service: AuditLogService, val userDAO: UserDAO, val swagger: Swagger)(implicit
  executor: ExecutionContext
) extends BaseController[AuditLog, Long] {
  val yamlFormat: YamlFormat[AuditLog] = FidesYamlProtocols.AuditLogFormat
  /* we will never post into the audit log */
  val inputMergeMap: Map[String, Any] = Map()

  def toPK(idStr: String): Try[Long] = Try { idStr.trim.toLong }
  get(
    "/:objectType/:id",
    operation(
      apiOperation[AuditLog](s"find all operations for audit log objectType/id")
        .summary(s"Find audit log operations for a specified object")
        .parameters(pathParam[String]("objectType").description(s"type of object to be fetched"))
        .parameters(pathParam[Int]("id").description(s"Id of objectType to be fetched"))
    )
  ) {
    val oid: Long = params("id").toLong //TODO safe to Long
    val typeName  = params("objectType")
    asyncResponse {
      service.dao
        .asInstanceOf[AuditLogDAO]
        .runAction(auditLogQuery.filter(a => a.typeName === typeName && a.objectId === oid).result)
    }
  }

}
