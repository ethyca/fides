package devtools.rating

import devtools.domain.policy.Policy
import devtools.domain.{Approval, Registry, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Tables.systemQuery
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** Wrapper class for running approvals, responsible for
  *
  * wrapping and fully populating objects to run approval checks on
  * generating and returning approval objects
  * storing approval objects where appropriate
  */
class Evaluator(val daos: DAOs)(implicit val executionContext: ExecutionContext) {

  private val systemEvaluator   = new SystemEvaluator(daos)
  private val registryEvaluator = new RegistryEvaluator(systemEvaluator)

// --------------------------------------------
  // system
  // --------------------------------------------

  //TODO disallow if user is not in same organization as system
  def systemEvaluate(
    sys: SystemObject,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] =
    generateSystemApproval(sys, "evaluate", userId, submitTag, submitMessage).flatMap(daos.approvalDAO.create)

  /** Generate an approval but does not save. */
  def systemDryRun(sys: SystemObject, userId: Long): Future[Approval] =
    generateSystemApproval(sys, "dry-run", userId, None, None)

  // --------------------------------------------
  // registry
  // --------------------------------------------

  def registryEvaluate(
    registry: Registry,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] =
    runRegistryEvaluate(registry, "evaluate", userId, submitTag, submitMessage).flatMap(daos.approvalDAO.create)

  def registryDryRun(registry: Registry, userId: Long): Future[Approval] =
    runRegistryEvaluate(registry, "dry-run", userId, None, None)

  // --------------------------------------------
  // evaluate
  // --------------------------------------------

  private def generateSystemApproval(
    system: SystemObject,
    actionType: String,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] = {
    val v: Future[(Iterable[Policy], Seq[SystemObject], Option[Long])] = for {
      policies            <- daos.policyDAO.findHydrated(_.organizationId === system.organizationId)
      dependentSystems    <- daos.systemDAO.findForFidesKeyInSet(system.systemDependencies, system.organizationId)
      currentVersionStamp <- daos.organizationDAO.getVersion(system.organizationId)
    } yield (policies, dependentSystems, currentVersionStamp)

    v.map((t: (Iterable[Policy], Seq[SystemObject], Option[Long])) => {
      val detailMap = systemEvaluator.evaluateSystem(system, t._2, t._1.toSeq)
      Approval(
        0,
        system.organizationId,
        Some(system.id),
        None,
        userId,
        t._3,
        submitTag,
        submitMessage,
        actionType,
        detailMap.overallApproval,
        Some(detailMap.toMap),
        None
      )
    })
  }

  private def runRegistryEvaluate(
    registry: Registry,
    action: String,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] = {

    val systemsFromRegistry: Future[Seq[SystemObject]] = registry.systems match {
      case Some(Left(ids))      => daos.systemDAO.db.run(systemQuery.filter(s => s.id inSet ids).result)
      case Some(Right(systems)) => Future.successful(systems)
      case _                    => daos.systemDAO.db.run(systemQuery.filter(s => s.registryId === registry.id).result)
    }

    val v: Future[(Iterable[Policy], Seq[SystemObject], Option[Long])] = for {
      policies            <- daos.policyDAO.findHydrated(_.organizationId === registry.organizationId)
      systems             <- systemsFromRegistry
      currentVersionStamp <- daos.organizationDAO.getVersion(registry.organizationId)
    } yield (policies, systems, currentVersionStamp)

    v.map {
      case (policies, systems, version) =>
        val detailMap: RegistryEvaluation = registryEvaluator.runEvaluation(systems, policies.toSeq)

        Approval(
          0,
          registry.organizationId,
          None,
          Some(registry.id),
          userId,
          version,
          submitTag,
          submitMessage,
          action,
          detailMap.overallApproval,
          Some(detailMap.toMap),
          None
        )

    }
  }

}
