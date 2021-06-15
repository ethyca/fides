package devtools.rating

import devtools.domain.enums._
import devtools.domain.policy.Policy
import devtools.domain.{Approval, Registry, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.systemQuery
import devtools.util.mapGrouping
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** Updated version of ratings */
class PolicyEvaluator(val policyRuleRater: PolicyRuleEvaluator, ratingsChecks: RegistryApprovalChecks, val daos: DAOs)(
  implicit val executionContext: ExecutionContext
) {

// --------------------------------------------
  // system
  // --------------------------------------------

  def systemEvaluate(sys: SystemObject, organizationId: Long, userId: Long): Future[Approval] =
    runEvaluation(Seq(sys), Some(sys.id), None, "evaluate", organizationId, userId).flatMap(daos.approvalDAO.create)

  def systemDryRun(sys: SystemObject, organizationId: Long, userId: Long): Future[Approval] =
    runEvaluation(Seq(sys), Some(sys.id), None, "dry-run", organizationId, userId)

  // --------------------------------------------
  // registry
  // --------------------------------------------

  def registryEvaluate(registry: Registry, organizationId: Long, userId: Long): Future[Approval] =
    runRegistryEvaluate(registry, "evaluate", organizationId, userId).flatMap(daos.approvalDAO.create)

  def registryDryRun(registry: Registry, organizationId: Long, userId: Long): Future[Approval] =
    runRegistryEvaluate(registry, "dry-run", organizationId, userId)

  /** Rate a single registry, which is assumed to be fully populated */
  private def runRegistryEvaluate(
    registry: Registry,
    action: String,
    organizationId: Long,
    userId: Long
  ): Future[Approval] = {

    // retrieve systems from the registry (if hydrated) or retrieve directly from the db.
    val systems: Future[Seq[SystemObject]] = registry.systems match {
      case Some(Left(ids))      => daos.systemDAO.db.run(systemQuery.filter(s => s.id inSet ids).result)
      case Some(Right(systems)) => Future.successful(systems)
      case _                    => daos.systemDAO.db.run(systemQuery.filter(s => s.registryId === registry.id).result)
    }

    systems.flatMap(runEvaluation(_, None, Some(registry.id), action, organizationId, userId))

  }

  // --------------------------------------------
  // evaluate
  // --------------------------------------------

  private def runEvaluation(
    systems: Seq[SystemObject],
    systemId: Option[Long],
    registryId: Option[Long],
    actionType: String,
    organizationId: Long,
    userId: Long
  ): Future[Approval] = {

    val v = for {
      policies <- daos.policyDAO.findHydrated(_.organizationId === organizationId)
      datasetNames = systems.flatMap(_.datasets).toSet
      datasets            <- daos.datasetDAO.findHydrated(_.fidesKey inSet datasetNames)
      currentVersionStamp <- daos.organizationDAO.getVersion(organizationId)
    } yield (policies, datasets, currentVersionStamp)

    v.flatMap {
      case (policies, datasets, version) =>
        val detailMap        = ratingsDetailMap(policies, systems)
        val validationErrors = ratingsChecks.validate(systems, datasets.toSeq)
        val mappedApproval   = extractApprovalStatus(detailMap)
        val overallApproval = if (validationErrors.hasErrors) { ApprovalStatus.FAIL }
        else mappedApproval

        Future.successful(
          Approval(
            0,
            organizationId,
            systemId,
            registryId,
            userId,
            version,
            actionType,
            overallApproval,
            Some(detailMap),
            Some(validationErrors.toMap),
            None
          )
        )
    }
  }

  // ------------------  support functions ------------------

  private def toApprovalStatus(action: PolicyAction): ApprovalStatus =
    action match {
      case PolicyAction.ACCEPT  => ApprovalStatus.PASS
      case PolicyAction.REJECT  => ApprovalStatus.FAIL
      case PolicyAction.REQUIRE => ApprovalStatus.MANUAL
    }

  /** return map of approval status -> [rules that returned that rating]
    *
    * (pass-> [r1, r2], fail=>
    */
  private def evaluateByRule(policy: Policy, system: SystemObject): Map[ApprovalStatus, Map[String, Seq[Long]]] = {

    val v = for {
      (d, i) <- system.declarations.zipWithIndex
      rules  <- policy.rules.getOrElse(Set())
      ra = policyRuleRater.matches(rules, d)
    } yield (ra, rules, i)

    val collectByAction = v.collect {
      case (Some(rating), rule, index) => (toApprovalStatus(rating), rule.fidesKey, index)
    }

    //e.g HashMap(FAIL -> HashMap(rule1 -> ArraySeq(0, 1), rule2 -> ArraySeq(0, 1)))
    mapGrouping(collectByAction, t => t.productElement(2), Seq(0, 1))
      .asInstanceOf[Map[ApprovalStatus, Map[String, Seq[Long]]]]

  }

  private def extractApprovalStatus(ratingsByRuleMap: Map[ApprovalStatus, _]): ApprovalStatus =
    if (ratingsByRuleMap.contains(ApprovalStatus.FAIL)) {
      ApprovalStatus.FAIL
    } else if (ratingsByRuleMap.contains(ApprovalStatus.MANUAL)) {
      ApprovalStatus.MANUAL
    } else {
      ApprovalStatus.PASS
    }
  /**
    *  Assemble ratings map
    * {"FAIL":
    *   {"system1":{
    *     "policy2":{"declarations":{"rule4":[0,1,2],"rule3":[0,1,2]}},
    *     "policy1":{"declarations":{"rule1":[0,1,2],"rule2":[0,1,2]}}}...
    *
    * @return
    */
  def ratingsDetailMap(
    policies: Iterable[Policy],
    systems: Iterable[SystemObject]
  ): Map[ApprovalStatus, _] = {

    val v: Iterable[(ApprovalStatus, String, String, Iterable[Map[String, Seq[Long]]])] = for {
      s <- systems
      p <- policies
      ratingsByRuleMap = evaluateByRule(p, s)
    } yield (extractApprovalStatus(ratingsByRuleMap), s.fidesKey, p.fidesKey, ratingsByRuleMap.values)

    /* Approval, system, policy, map
     *  =>
     * {"approval": { "system": {"policy" {"rule1":[declarations...] }
     *
     * */

    v.groupBy(_._1)
      .map(t1 =>
        t1._1 -> //approval;
          t1._2
            .groupBy(_._2)
            .map(t2 =>
              t2._1 -> //system
                t2._2
                  .groupBy(_._3)
                  .map(t3 =>
                    t3._1 -> //policy
                      {
                        val maps: Seq[Map[String, _]] = t3._2.flatMap(_._4).asInstanceOf[Seq[Map[String, _]]]
                        "declarations" -> maps.fold(Map())((a, b) => a ++ b)
                      }
                  )
                  .filterNot((t: (String, (String, Map[String, _]))) => t._2._2.isEmpty)
            )
      )

  }
}
