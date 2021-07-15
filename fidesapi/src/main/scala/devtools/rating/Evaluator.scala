package devtools.rating

import devtools.domain.policy.Policy
import devtools.domain.{Approval, Dataset, Registry, SystemObject}
import devtools.persist.dao.DAOs
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** for a given set of systems, a set of all relevant objects (hydrated)
  * that will be needed for running an evaluation.
  * - system[s] - populated with privacy declarations as a Map[fidesKey -> system]
  * - Seq[policies] - populated with privacy rules
  * - datasets - populated as a map [fidesKey -> dataset]
  * - current version stamp
  * -
  */
final case class EvaluationObjectSet(
  systems: Map[String, SystemObject],
  policies: Seq[Policy],
  datasets: Map[String, Dataset],
  versionStamp: Option[Long]
)

/** Wrapper class for running approvals, responsible for
  *
  * wrapping and fully populating objects to run approval checks on
  * generating and returning approval objects
  * storing approval objects where appropriate
  */
class Evaluator(val daos: DAOs)(implicit val executionContext: ExecutionContext) {

  private val systemEvaluator = new SystemEvaluator(daos)

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
    generateRegistryApproval(registry, "evaluate", userId, submitTag, submitMessage).flatMap(daos.approvalDAO.create)

  def registryDryRun(registry: Registry, userId: Long): Future[Approval] =
    generateRegistryApproval(registry, "dry-run", userId, None, None)

  // --------------------------------------------
  // evaluate
  // --------------------------------------------

  /** starting from a system or group of systems, retrieve all objects we will need in order to
    * process the evaluation.
    */
  def retrievePopulated(systems: Seq[SystemObject]): Future[EvaluationObjectSet] = {
    if (systems.isEmpty) {
      Future.successful(EvaluationObjectSet(Map(), Seq(), Map(), None))
    } else {
      val organizationId = systems.head.organizationId
      //will also need to retrieve systems that are referenced by dependent systems:
      val declaredFidesKeys         = systems.map(_.fidesKey).toSet
      val dependentSystemsFidesKeys = systems.flatMap(_.systemDependencies).toSet.diff(declaredFidesKeys)
      val allSystemKeys             = declaredFidesKeys ++ dependentSystemsFidesKeys
      val hydratedSystems           = systems.filter(_.privacyDeclarations.nonEmpty).toSet
      val unhydratedSystemFidesKeys = allSystemKeys.diff(hydratedSystems.map(_.fidesKey))
      for {
        policies <- daos.policyDAO.findHydrated(_.organizationId === organizationId)
        newlyHydratedSystems <- daos.systemDAO.findHydrated(s =>
          (s.fidesKey inSet unhydratedSystemFidesKeys) && (s.organizationId === organizationId)
        )
        allHydratedSystems = newlyHydratedSystems ++ hydratedSystems
        datasets <- {
          val referencedDatasets = {
            val declarations = allHydratedSystems.flatMap(s => s.privacyDeclarations.getOrElse(Seq()))
            //this can be either dataset, dataset.field, dataset.table.field...
            val datasetFullNames = declarations.flatMap(_.datasetReferences)
            datasetFullNames.map(Dataset.baseName).toSet
          }
          daos.datasetDAO.findHydrated(s =>
            (s.fidesKey inSet referencedDatasets) && (s.organizationId === organizationId)
          )
        }
        currentVersionStamp <- daos.organizationDAO.getVersion(organizationId)
      } yield EvaluationObjectSet(
        allHydratedSystems.toSet.map((s: SystemObject) => s.fidesKey -> s).toMap,
        policies.toSeq,
        datasets.map(s => s.fidesKey -> s).toMap,
        currentVersionStamp
      )

    }
  }

  private def generateSystemApproval(
    system: SystemObject,
    actionType: String,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] = {

    retrievePopulated(Seq(system)).map(eo => {
      val detailMap = systemEvaluator.evaluateSystem(system.fidesKey, eo)
      Approval(
        0,
        system.organizationId,
        Some(system.id),
        None,
        userId,
        eo.versionStamp,
        submitTag,
        submitMessage,
        actionType,
        detailMap.overallApproval,
        Some(detailMap.toMap),
        None
      )
    })
  }

  private def generateRegistryApproval(
    registry: Registry,
    action: String,
    userId: Long,
    submitTag: Option[String],
    submitMessage: Option[String]
  ): Future[Approval] = {

    val systemsFromRegistry: Future[Iterable[SystemObject]] = registry.systems match {
      case Some(Left(ids))      => daos.systemDAO.findHydrated(s => s.id inSet ids)
      case Some(Right(systems)) => Future.successful(systems)
      case _ =>
        daos.systemDAO.findHydrated(s =>
          (s.registryId === registry.id) && (s.organizationId === registry.organizationId)
        )

    }
    for {
      s <- systemsFromRegistry
      sq = s.toSeq
      eo <- retrievePopulated(sq)
      eval = RegistryEvaluator.evaluateRegistry(sq.map(_.fidesKey), eo, systemEvaluator)
      approval = Approval(
        0,
        registry.organizationId,
        None,
        Some(registry.id),
        userId,
        eo.versionStamp,
        submitTag,
        submitMessage,
        action,
        eval.overallApproval,
        Some(eval.toMap),
        None
      )

    } yield approval

  }

}
