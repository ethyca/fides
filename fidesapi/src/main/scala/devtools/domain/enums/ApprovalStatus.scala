package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait ApprovalStatus {}

object ApprovalStatus extends EnumSupport[ApprovalStatus] {
  case object PASS   extends ApprovalStatus
  case object MANUAL extends ApprovalStatus
  case object FAIL   extends ApprovalStatus
  /** Approval could not be processed because there are error conditions */
  case object ERROR extends ApprovalStatus
  val values = Set(PASS, MANUAL, FAIL, ERROR)

}
