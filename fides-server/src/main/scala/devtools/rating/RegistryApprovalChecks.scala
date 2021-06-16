package devtools.rating

import devtools.domain.policy.Declaration
import devtools.domain._
import devtools.persist.dao.DAOs
import devtools.util.CycleDetector.collectCycleErrors
import devtools.validation.MessageCollector

/** Checks performed on fully validated rating objects as part of the approval process.
  *
  * missing datasets
  * dependency cycle errors
  * missing systems
  * datasets - dependency mismatch
  */

class RegistryApprovalChecks(val daos: DAOs) {

  def validate(systems: Iterable[SystemObject], datasets: Iterable[Dataset]): MessageCollector = {
    val errors = new MessageCollector
    cycleCheck(systems, errors)
    validateDatasetsExist(systems, datasets, errors)
    checkVersionStampDependencies(systems, datasets, errors)
    systems.foreach(checkDatasetDependencies(_, datasets, errors))
    systems.foreach(checkDeclarationsOfDependentSystems(_, systems, errors))
    errors
  }
  /** check for dependency cycles in the "declaredSystems" member of systems.
    */
  def cycleCheck(systems: Iterable[SystemObject], errors: MessageCollector): Unit = {
    println(s" sysTEMS: ${systems.map(s => s.fidesKey + s.systemDependencies + "|\n   ")}")
    val m: Map[String, Set[String]]  = systems.map(s => s.fidesKey -> s.systemDependencies).toMap
    val allDeclarations: Set[String] = m.values.flatten.toSet
    val diff                         = allDeclarations.diff(m.keySet)
    if (diff.nonEmpty) {
      errors.addError(s"These systems were declared as dependencies but were not found :[${diff.mkString(",")}]")
    }
    collectCycleErrors(m.toSeq, errors)
  }

  /** Require that all values listed as a dependent datasets exist */
  def validateDatasetsExist(
    systems: Iterable[SystemObject],
    datasets: Iterable[Dataset],
    errors: MessageCollector
  ): Unit = {
    val datasetKeys      = systems.flatMap(_.datasets).toSet
    val foundDatasetKeys = datasets.map(_.fidesKey).toSet
    val diff             = datasetKeys.diff(foundDatasetKeys)
    if (diff.nonEmpty) {
      errors.addError(s"These datasets were declared as dependencies but were not found:[${diff.mkString(",")}]")
    }
    systems.foreach(checkDatasetDependencies(_, datasets, errors))
  }

  /** Check system declarations and warn if there are declared types in the dataset that have not been declared
    * in the system
    */
  def checkDatasetDependencies(
    systemObject: SystemObject,
    datasets: Iterable[Dataset],
    errors: MessageCollector
  ): Unit = {
    //data categories, data qualifiers
    //1. map of all declared (qualifier -> categories) in datasets
    //2. map of all declared (qualifier -> categories) in systems

    //for all in system (and children) if not in dataset, error

    //system {qualifier -> categories }
    val categoriesByQualifierInSystem: Map[DataQualifierName, Set[DataCategoryName]] = systemObject.declarations
      .map(d => (d.dataQualifier, d.dataCategories))
      .groupBy(_._1)
      .map((t: (DataQualifierName, Seq[(DataQualifierName, Set[DataCategoryName])])) => t._1 -> t._2.map(_._2))
      .map(t => t._1 -> daos.dataCategoryDAO.mergeAndReduce(systemObject.organizationId, t._2.flatten.toSet))

    def categoriesForQualifier(dataQualifier: DataQualifierName, dataset: Dataset): Set[DataCategoryName] = {
      val categories: Set[DataCategoryName] = dataset.categoriesForQualifiers(
        daos.dataQualifierDAO.childrenOfInclusive(systemObject.organizationId, dataQualifier)
      )
      daos.dataCategoryDAO.mergeAndReduce(systemObject.organizationId, categories)
    }

    datasets.foreach(ds => {
      categoriesByQualifierInSystem.foreach {
        case (qualifier, categories) =>
          val datasetCategories = categoriesForQualifier(qualifier, ds)
          val diff              = datasetCategories.diff(categories)
          if (diff.nonEmpty) {
            errors.addWarning(
              s"These categories exist for qualifer $qualifier in the declared dataset ${ds.fidesKey} but do not appear with that qualifier in the dependant system ${systemObject.fidesKey}:[${diff
                .mkString(",")}]"
            )
          }
      }
    })

  }

  def checkVersionStampDependencies(
    systems: Iterable[SystemObject],
    datasets: Iterable[Dataset],
    errors: MessageCollector
  ): Unit = {

    /** Compare version stamps; true if neither value is None and ts2 later than ts1 */
    def laterThan(vs1: Option[Long], vs2: Option[Long]): Boolean =
      (vs1, vs2) match {
        case (Some(v1), Some(v2)) => v2 > v1
        case _                    => false
      }

    val systemMap  = systems.map(s => s.fidesKey -> s).toMap
    val datasetMap = datasets.map(d => d.fidesKey -> d).toMap
    systems.foreach((s: SystemObject) => {
      s.systemDependencies.foreach(dep =>
        systemMap.get(dep) match {
          case Some(dependentSystem: SystemObject) if laterThan(s.versionStamp, dependentSystem.versionStamp) =>
            errors.addWarning(
              s"${s.fidesKey} declares the system ${dependentSystem.fidesKey} as a dependency, but ${dependentSystem.fidesKey} has been more recently updated than ${s.fidesKey}"
            )

          case _ =>
        }
      )
      s.datasets.foreach(dep =>
        datasetMap.get(dep) match {
          case Some(dependentDataset: Dataset) if laterThan(s.versionStamp, dependentDataset.versionStamp) =>
            errors.addWarning(
              s"${s.fidesKey} declares the dataset ${dependentDataset.fidesKey} as a dependency, but ${dependentDataset.fidesKey} has been more recently updated than ${s.fidesKey}"
            )
          case _ =>
        }
      )
    })
  }

  /** for all dependent systems, check if privacy declarations includes things that are not in the privacy set of this system.
    * Assumes that all dependent systems are populated in the allRegistrySystems variable
    */
  def checkDeclarationsOfDependentSystems(
    systemObject: SystemObject,
    allRegistrySystems: Iterable[SystemObject],
    errors: MessageCollector
  ): Unit = {
    val dependentSystems   = allRegistrySystems.filter(s => systemObject.systemDependencies.contains(s.fidesKey))
    val mergedDependencies = mergeDeclarations(systemObject.organizationId, systemObject.declarations)
    dependentSystems.foreach(ds => {
      val mergedDependenciesForDs = mergeDeclarations(systemObject.organizationId, ds.declarations)
      val diff                    = diffDeclarations(systemObject.organizationId, mergedDependenciesForDs, mergedDependencies)
      if (diff.nonEmpty) {
        errors.addWarning(
          s"The system ${ds.fidesKey} includes privacy declarations that do not exist in ${systemObject.fidesKey} : $diff"
        )
      }
    })
  }

  /**
    * For all declarations
    *  - match:
    *    - they have the same data use
    *    - they have the same data qualifier
    *
    * data subject categories are the mergeDeclarations of both data subject categories
    * data categories are the mergeDeclarations of both data categories
    *
    * where "mergeDeclarations" means:
    *      - mergeAndReduce both sets of values
    *      - reduce both sets of values using TreeCache mergeAndReduce
    */

  def mergeDeclarations(organizationId: Long, declarations: Iterable[Declaration]): Seq[Declaration] = {
    declarations
      .groupBy(d => (d.dataQualifier, d.dataUse))
      .map { t =>
        val categories = daos.dataCategoryDAO.mergeAndReduce(organizationId, t._2.flatMap(_.dataCategories).toSet)
        val subjectCategories =
          daos.dataSubjectCategoryDAO.mergeAndReduce(organizationId, t._2.flatMap(_.dataSubjectCategories).toSet)
        Declaration("merged", categories, t._1._2, t._1._1, subjectCategories)
      }
      .toSeq
  }

  def diffDeclarations(organizationId: Long, a: Iterable[Declaration], b: Iterable[Declaration]): Set[Declaration] = {

    val l = mergeDeclarations(organizationId, a)
    val r = mergeDeclarations(organizationId, b)

    val rGrouped: Map[(DataQualifierName, DataUseName), Seq[Declaration]] = r.groupBy(d => (d.dataQualifier, d.dataUse))

    val grouped: Seq[Declaration] = l
      .groupBy(d => (d.dataQualifier, d.dataUse))
      .map { t: ((DataQualifierName, DataUseName), Seq[Declaration]) =>
        val rVals: Seq[Declaration] = rGrouped.getOrElse(t._1, Seq())
        val rCategories             = rVals.flatMap(_.dataCategories).toSet
        val rSubjectCategories      = rVals.flatMap(_.dataSubjectCategories).toSet

        val lCategories        = t._2.flatMap(_.dataCategories).toSet
        val lSubjectCategories = t._2.flatMap(_.dataSubjectCategories).toSet

        val categoryDiff = daos.dataCategoryDAO.diff(organizationId, rCategories, lCategories)
        val subjectCategoryDiff =
          daos.dataSubjectCategoryDAO.diff(organizationId, rSubjectCategories, lSubjectCategories)

        Declaration("merged", categoryDiff, t._1._2, t._1._1, subjectCategoryDiff)
      }
      .toSeq

    grouped.filter(d => d.dataCategories.nonEmpty || d.dataSubjectCategories.nonEmpty).toSet
  }
}
