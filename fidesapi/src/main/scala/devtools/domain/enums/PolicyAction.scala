package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait PolicyAction {}

object PolicyAction extends EnumSupport[PolicyAction] {

  case object ACCEPT  extends PolicyAction
  case object REJECT  extends PolicyAction
  case object REQUIRE extends PolicyAction
  val values = Set(ACCEPT, REJECT, REQUIRE)
}
