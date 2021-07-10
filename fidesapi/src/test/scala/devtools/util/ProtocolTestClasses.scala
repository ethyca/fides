package devtools.util

import devtools.domain.enums._

object ProtocolTestClasses {
  final case class Simple(i: Int, name: String)

  final case class Thing(color: String, priority: Int, count: Option[Int])

  final case class ThingHolder(name: String, things: List[Thing])

  final case class EitherHolder(name: String, things: Option[Either[Seq[Int], Seq[Simple]]])

  final case class EnumHolder(
    approval: ApprovalStatus,
    auditAction: AuditAction,
    policyAction: PolicyAction,
    ruleInclusion: RuleInclusion,
    role: Role
  )

}
