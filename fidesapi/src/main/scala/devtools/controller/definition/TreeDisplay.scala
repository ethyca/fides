package devtools.controller.definition

import devtools.domain.definition.{CanBeTree, IdType, TreeItem}

import scala.util.{Failure, Success}

/** Crud Controller functions common to types that can be treated as hierarchical
  * trees:
  *
  * GET "/:id/taxonomy" - children of id in a tree display.
  * GET /taxonomy - entire tree of values for this type.
  */

trait TreeDisplay[T <: IdType[T, PK] with CanBeTree[PK, TI], PK, TI <: TreeItem[TI, PK]] {
  self: BaseController[T, PK] =>

  def taxonomyGetAll(): Iterable[TI]

  def taxonomyGetById(id: PK): Option[TI]

  get(
    "/taxonomy",
    operation(
      apiOperation[Iterable[T]](s"$typeName taxonomy")
        .summary(s"Tree structure of $typeName data")
        .description(s"Display parent-child arrangement of all $typeName values")
    )
  ) {
    ApiResponse.success(taxonomyGetAll())
  }

  /** Find By Id/History */
  get(
    "/:id/taxonomy",
    operation(
      apiOperation[T](s"$typeName taxonomy by Id")
        .summary(s"Tree structure of $typeName data for children of the given id")
        .description(s"$typeName @ id and all child values")
    )
  )(toPK(params("id")) match {
    case Success(id) => ApiResponse.fromOption(taxonomyGetById(id))
    case Failure(e)  => ApiResponse.failure(e)
  })

}
