package devtools.controller

import devtools.controller.definition.ApiResponse.asyncResponse
import devtools.controller.definition.ControllerSupport
import devtools.persist.dao.DAOs
import org.scalatra.swagger.Swagger
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** Admin functions controller.
  * Note that this is a placeholder implementation with functionality to simplify testing. Requires authentication.
  */
class AdminController(val daos: DAOs, val swagger: Swagger)(implicit val executor: ExecutionContext)
  extends ControllerSupport {
  val applicationDescription: String = "admin"
  /** wipe an organization */
  delete(
    "/organization/:id",
    operation(
      apiOperation[Int](s"delete all sub-objects in an organization; leaves the organization intact")
        .summary(s"Delete an organizations members by id")
        .parameters(pathParam[Long]("id").description(s"Id of the organization to be cleaned"))
    )
  ) {
    withIntParameter(
      params("id"),
      request,
      (id, _) => {

        val responses: Future[(Int, Int, Int, Int, Int, Int, Int, Int)] = for {
          a <- daos.approvalDAO.delete(_.organizationId === id)
          b <- daos.auditLogDAO.delete(_.organizationId === id)
          c <- daos.dataCategoryDAO.delete(_.organizationId === id)
          d <- daos.dataQualifierDAO.delete(_.organizationId === id)
          e <- daos.dataUseDAO.delete(_.organizationId === id)
          f <- daos.systemDAO.delete(_.organizationId === id)
          g <- daos.dataSubjectCategoryDAO.delete(_.organizationId === id)
          h <- daos.userDAO.delete(_.organizationId === id)

        } yield (a, b, c, d, e, f, g, h)

        daos.dataCategoryDAO.cacheDelete(id)
        daos.dataQualifierDAO.cacheDelete(id)
        daos.dataUseDAO.cacheDelete(id)
        daos.dataSubjectCategoryDAO.cacheDelete(id)

        asyncResponse(
          responses.map(t =>
            Map(
              "Approvals"             -> t._1,
              "AuditLogs"             -> t._2,
              "DataCategories"        -> t._3,
              "DataQualifiers"        -> t._4,
              "DataUses"              -> t._5,
              "Systems"               -> t._6,
              "DataSubjectCategories" -> t._7,
              "Users"                 -> t._8
            )
          )
        )

      }
    )
  }

}
