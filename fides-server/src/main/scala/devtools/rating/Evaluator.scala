package devtools.rating

import devtools.domain.policy.Policy
import devtools.domain.{Approval, Dataset, Registry, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.systemQuery
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
  def systemEvaluate(sys: SystemObject, userId: Long): Future[Approval] =
    generateSystemApproval(sys, "evaluate", userId).flatMap(daos.approvalDAO.create)

  def systemDryRun(sys: SystemObject, userId: Long): Future[Approval] =
    generateSystemApproval(sys, "dry-run", userId)

  // --------------------------------------------
  // registry
  // --------------------------------------------

  def registryEvaluate(registry: Registry, userId: Long): Future[Approval] =
    runRegistryEvaluate(registry, "evaluate", userId).flatMap(daos.approvalDAO.create)

  def registryDryRun(registry: Registry, userId: Long): Future[Approval] =
    runRegistryEvaluate(registry, "dry-run", userId)

  // --------------------------------------------
  // evaluate
  // --------------------------------------------

  private def generateSystemApproval(system: SystemObject, actionType: String, userId: Long): Future[Approval] = {
    val v: Future[(Iterable[Policy], Seq[SystemObject], Iterable[Dataset], Option[Long])] = for {
      policies            <- daos.policyDAO.findHydrated(_.organizationId === system.organizationId)
      dependentSystems    <- daos.systemDAO.findForFidesKeyInSet(system.systemDependencies, system.organizationId)
      datasets            <- daos.datasetDAO.findHydrated(_.fidesKey inSet system.datasets)
      currentVersionStamp <- daos.organizationDAO.getVersion(system.organizationId)
    } yield (policies, dependentSystems, datasets, currentVersionStamp)

    v.map((t: (Iterable[Policy], Seq[SystemObject], Iterable[Dataset], Option[Long])) => {
      val detailMap = systemEvaluator.evaluateSystem(system, t._2, t._3.toSeq, t._1.toSeq)
      Approval(
        0,
        system.organizationId,
        Some(system.id),
        None,
        userId,
        t._4,
        actionType,
        detailMap.overallApproval,
        Some(detailMap.toMap),
        None,
        None
      )
    })
  }

  private def runRegistryEvaluate(registry: Registry, action: String, userId: Long): Future[Approval] = {

    val systemsFromRegistry: Future[Seq[SystemObject]] = registry.systems match {
      case Some(Left(ids))      => daos.systemDAO.db.run(systemQuery.filter(s => s.id inSet ids).result)
      case Some(Right(systems)) => Future.successful(systems)
      case _                    => daos.systemDAO.db.run(systemQuery.filter(s => s.registryId === registry.id).result)
    }

    val v: Future[(Iterable[Policy], Seq[SystemObject], Iterable[Dataset], Option[Long])] = for {
      policies <- daos.policyDAO.findHydrated(_.organizationId === registry.organizationId)
      systems  <- systemsFromRegistry
      datasetNames = systems.flatMap(_.datasets).toSet
      datasets            <- daos.datasetDAO.findHydrated(_.fidesKey inSet datasetNames)
      currentVersionStamp <- daos.organizationDAO.getVersion(registry.organizationId)
    } yield (policies, systems, datasets, currentVersionStamp)

    v.map {
      case (policies, systems, datasets, version) =>
        val detailMap: RegistryEvaluation = registryEvaluator.runEvaluation(systems, datasets.toSeq, policies.toSeq)

        Approval(
          0,
          registry.organizationId,
          None,
          Some(registry.id),
          userId,
          version,
          action,
          detailMap.overallApproval,
          Some(detailMap.toMap),
          None,
          None
        )

    }
  }

}
