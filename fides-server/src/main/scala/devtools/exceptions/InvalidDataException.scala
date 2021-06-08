package devtools.exceptions

final case class InvalidDataException(error: String) extends BaseFidesException("Invalid Data", Seq(error)) {}
