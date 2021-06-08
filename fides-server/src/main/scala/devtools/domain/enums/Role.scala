package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait Role {}

object Role extends EnumSupport[Role] {
  case object USER  extends Role
  case object ADMIN extends Role

  val values = Set(USER, ADMIN)
}
