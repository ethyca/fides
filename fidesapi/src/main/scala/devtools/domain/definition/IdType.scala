package devtools.domain.definition

/** Domain type with an id member. */
trait IdType[E, PK] {
  def id: PK
  /** Supply a copy of this object with an altered id. */
  def withId(id: PK): E

}
