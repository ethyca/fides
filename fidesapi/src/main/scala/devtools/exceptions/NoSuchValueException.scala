package devtools.exceptions

final case class NoSuchValueException(typeName: String, value: Any)
  extends BaseFidesException("No such value", Seq(s"No $typeName ${value.toString} exists.")) {}
