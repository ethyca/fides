package devtools.controller.definition

import devtools.controller.definition.ApiResponse._
import devtools.domain.definition.IdType

import scala.util.{Failure, Success, Try}

/** Crud Controller functions common to domain types with a Long primary key.
  *
  * - READ: get /id
  * - DELETE: delete /id
  * - CREATE: post
  * - UPDATE post /id
  */
trait LongPK[T <: IdType[T, Long]] {
  self: BaseController[T, Long] =>

  val inputMergeMap: Map[String, Any] = Map("id" -> 0L)

  /** Ensure that the id parameter is parse-able. */
  def toPK(idStr: String): Try[Long] = Try { idStr.trim.toLong }

  /** Find By Id */
  get(
    "/:id",
    operation(
      apiOperation[T](s"find${typeName}ById")
        .summary(s"Find $typeName by id")
        .parameters(pathParam[Int]("id").description(s"Id of $typeName to be fetched"))
    )
  )(withIntParameter(params("id"), request, (id, _) => asyncOptionResponse(service.findById(id, requestContext))))

  /** Delete */
  delete(
    "/:id",
    operation(
      apiOperation[Int](s"delete${typeName}byId")
        .summary(s"Delete $typeName by id")
        .parameters(pathParam[Int]("id").description(s"Id of $typeName to be deleted"))
    )
  )(withIntParameter(params("id"), request, (id, _) => asyncResponse(service.delete(id, requestContext))))

  /** Create */
  post(
    "/",
    operation(
      apiOperation[T](s"create $typeName")
        .summary(s"Create a new instance of $typeName")
    )
  ) {
    ingest(request.body, request.getHeader("Content-Type"), inputMergeMap) match {
      case Success(t) => asyncResponse(service.create(t, requestContext))

      case Failure(exception) => failure(exception)
    }
  }

  /** Update */
  post(
    "/:id",
    operation(
      apiOperation[T]("update by id")
        .summary(s"update $typeName by id")
        .parameters(pathParam[Int]("id").description(s"Id of $typeName to be updated"))
    )
  )(
    withIntParameter(
      params("id"),
      request,
      (id, _) => {

        val t = ingest(request.body, request.getHeader("Content-Type"), Map("id" -> id))

        t match {
          case Success(t) =>
            ApiResponse.asyncOptionResponse(service.update(t, requestContext).flatMap { _ =>
              service.findById(id, requestContext)
            })

          case Failure(e: Throwable) => ApiResponse.failure(e)
        }
      }
    )
  )

}
