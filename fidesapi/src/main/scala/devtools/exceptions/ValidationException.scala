package devtools.exceptions

final case class ValidationException(override val errors: Seq[String])
  extends BaseFidesException("Validation Error", errors) {}
