package devtools.rating

import devtools.domain.SystemObject
import devtools.domain.enums.ApprovalStatus
import devtools.util.CycleDetector.collectCycleErrors

final case class RegistryEvaluation(
  /** map of status to {policy.rule -> [matching declaration names]} */
  systemEvaluations: Map[String, SystemEvaluation],
  /** A list of warning strings collected as we cycle through evaluation rules */
  warnings: Seq[String],
  overallApproval: ApprovalStatus
) {

  def toMap: Map[String, Any] = {
    val overall: Map[ApprovalStatus, Iterable[String]] =
      systemEvaluations.map(t => (t._2.overallApproval, t._1)).groupBy(_._1).map(t => t._1 -> t._2.values)

    Map("overall" -> overall, "evaluations" -> systemEvaluations.map(t => t._1 -> t._2.toMap), "warnings" -> warnings)
  }
}

object RegistryEvaluator {

  /** Don't allow a cycle in the system graph. */
  def cycleCheck(systems: Seq[SystemObject]): Seq[String] =
    collectCycleErrors(systems.map(s => s.fidesKey -> s.systemDependencies))

  /** evaluate all systems in the registry. fides key for relevant systems are provided
    * since the EvaluationObjectSet may contain systems that are only referenced in
    * System.systemDependencies.
    */
  def evaluateRegistry(
    fidesKeys: Seq[String],
    eo: EvaluationObjectSet,
    systemEvaluator: SystemEvaluator
  ): RegistryEvaluation = {

    val cycleWarnings = cycleCheck(eo.systems.values.toSeq)

    val systemEvaluations: Map[String, SystemEvaluation] = fidesKeys
      .map(fk => fk -> systemEvaluator.evaluateSystem(fk, eo))
      .toMap

    val overallApproval = {
      if (systemEvaluations.values.exists(_.errors.nonEmpty)) {
        ApprovalStatus.ERROR
      } else {
        val approvals = systemEvaluations.values.map(_.overallApproval).toSet

        if (approvals.contains(ApprovalStatus.FAIL)) {
          ApprovalStatus.FAIL
        } else if (approvals.contains(ApprovalStatus.MANUAL)) {
          ApprovalStatus.MANUAL
        } else {
          ApprovalStatus.PASS
        }

      }
    }
    RegistryEvaluation(systemEvaluations, cycleWarnings, overallApproval)

  }

}
