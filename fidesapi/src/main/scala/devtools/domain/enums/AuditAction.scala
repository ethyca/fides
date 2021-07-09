package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait AuditAction {}

object AuditAction extends EnumSupport[AuditAction] {
  case object CREATE extends AuditAction
  case object UPDATE extends AuditAction
  case object DELETE extends AuditAction

  val values = Set(CREATE, UPDATE, DELETE)
}
