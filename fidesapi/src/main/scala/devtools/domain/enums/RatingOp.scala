package devtools.domain.enums

import devtools.domain.definition.EnumSupport

sealed trait RatingOp {}
/** An operation that submits and returns an approval */
object RatingOp extends EnumSupport[RatingOp] {

  case object DRY_RUN extends RatingOp

  case object SUBMIT_CREATE extends RatingOp

  case object SUBMIT_UPDATE extends RatingOp

  val values = Set(DRY_RUN, SUBMIT_UPDATE, SUBMIT_CREATE)

}
