package devtools.rating

import devtools.domain.SystemObject
import devtools.domain.enums.ApprovalStatus
import devtools.domain.policy.Policy
import devtools.util.CycleDetector.collectCycleErrors

import scala.concurrent.ExecutionContext

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

class RegistryEvaluator(val systemEvaluator: SystemEvaluator)(implicit val executionContext: ExecutionContext) {

  /** Don't allow a cycle in the system graph. */
  def cycleCheck(systems: Seq[SystemObject]): Seq[String] =
    collectCycleErrors(systems.map(s => s.fidesKey -> s.systemDependencies))

  /** Evaluate and generate an approval for the given sequence of systems and datasets.
    * This method assumes that all systems and datasets have been populated.
    */
  def runEvaluation(systems: Seq[SystemObject], policies: Seq[Policy]): RegistryEvaluation = {
    val cycleWarnings = cycleCheck(systems)

    val systemEvaluations: Map[String, SystemEvaluation] = systems
      .map(sys =>
        sys.fidesKey -> systemEvaluator.evaluateSystem(
          sys,
          systems.filter(dependentSystem => sys.systemDependencies.contains(dependentSystem.fidesKey)),
          policies
        )
      )
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
