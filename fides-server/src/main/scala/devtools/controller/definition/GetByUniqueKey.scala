package devtools.controller.definition

import devtools.controller.definition.ApiResponse._
import devtools.domain.definition.IdType
import devtools.persist.service.definition.{Service, UniqueKeySearch}

/** Crud Controller functions supporting a find by unique key search. For most types this is
  * the fides key.
  */
trait GetByUniqueKey[T <: IdType[T, Long]] {
  self: BaseController[T, Long] =>

  val service: Service[T, Long] with UniqueKeySearch[T]

  /** Find By Unique key */
  get(
    "/find/:key",
    operation(
      apiOperation[T](s"find${typeName}ByKey")
        .summary(s"Find $typeName by unique key")
        .parameters(pathParam[Int]("key").description(s"Unique key string of $typeName to be fetched"))
    )
  )(
    asyncOptionResponse(
      service
        .asInstanceOf[UniqueKeySearch[T]]
        .findByUniqueKey(requestContext.organizationId.getOrElse(-1), params("key"))
    )
  )

}
