package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait ApprovalStatus {}

object ApprovalStatus extends EnumSupport[ApprovalStatus] {
  case object PASS   extends ApprovalStatus
  case object FAIL   extends ApprovalStatus
  case object MANUAL extends ApprovalStatus

  val values = Set(PASS, FAIL, MANUAL)

}
