package devtools.util

/** Specification for api pagination parameters. */
final case class Pagination(limit: Int = 100, offset: Int = 0)

object Pagination {
  def unlimited: Pagination = Pagination(Int.MaxValue, 0)
}
