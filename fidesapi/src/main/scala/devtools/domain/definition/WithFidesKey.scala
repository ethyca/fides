package devtools.domain.definition

/** Domain object that contains a Fides key, as well as some other common values. */
trait WithFidesKey[E, PK] extends IdType[E, PK] {
  /** a unique identifier. */
  def fidesKey: String
  /** an optional name */
  def name: Option[String]
  /** an optional name */
  def description: Option[String]

}
