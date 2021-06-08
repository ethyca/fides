package devtools.domain.enums

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.definition.EnumSupport

sealed trait RuleInclusion {}

object RuleInclusion extends EnumSupport[RuleInclusion] {

  case object ALL  extends RuleInclusion
  case object ANY  extends RuleInclusion
  case object NONE extends RuleInclusion

  val values = Set(ALL, ANY, NONE)
}

/** A grouping of an inclusion, like "ALL", or "ANY" with a list of values. */
final case class PolicyValueGrouping(inclusion: RuleInclusion, values: Set[String]) extends LazyLogging {}
