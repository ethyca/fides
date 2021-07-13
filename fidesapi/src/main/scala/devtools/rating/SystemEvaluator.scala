package devtools.rating

import devtools.domain._
import devtools.domain.enums._
import devtools.domain.policy.{Policy, PolicyRule}
import devtools.persist.dao.DAOs
import devtools.util.mapGrouping
import devtools.validation.MessageCollector

import scala.concurrent.ExecutionContext

final case class SystemEvaluation(
  /** map of status to {policy.rule -> [matching declaration names]} */
  statusMap: Map[ApprovalStatus, Map[String, Seq[String]]],
  /** A list of warning strings collected as we cycle through evaluation rules */
  warnings: Seq[String],
  /** A list of error strings collected as we cycle through evaluation rules */
  errors: Seq[String],
  overallApproval: ApprovalStatus
) {

  def toMap: Map[String, Any] =
    statusMap.map(t => t._1.toString -> t._2) ++ Seq("warnings" -> warnings, "errors" -> errors)
}

/** Updated version of ratings */
class SystemEvaluator(val daos: DAOs)(implicit val executionContext: ExecutionContext) {

  private val policyRuleEvaluator = new PolicyRuleEvaluator(daos)

  /** Check system declarations and warn if there are declared types in the datasets that don't match
    * those in the privacy declaration(s).
    */
  def checkPrivacyDeclaration(
    privacyDeclaration: PrivacyDeclaration,
    datasets: Map[String, Dataset],
    mc: MessageCollector
  ): Unit = {

    /** Split dataset.field into (dataset,field) */
    def splitRef(s: String) = {
      val i    = s.indexOf('.')
      val head = if (i == -1) s else s.substring(0, i)
      val tail = if (i == -1 || i == s.length) "" else s.substring(i + 1)
      (head, tail)
    }

    /** For the given dataset map of {qualifier -> set[categories]}, compare with the privacy declaration and return a possible list of
      * category fides keys that are not children of the categories listed in the privacy declaration under that qualifier.
      *
      * For example, if the privacy declaration contains {dataQualifier = "a" ->  dataCategories = ["b","c", "d"]} and the
      * dataset contains {dataQualifier = "a or child of a" ->  dataCategories = ["b or child of b", "c or child of c", "e", "f"]}
      * this method should return ["e","f"].
      *
      * If the qualifier in the dataset is not == to or a child of the qualifier in the privacy declaration this method will return None
      */
    def gamutCheck(
      pd: PrivacyDeclaration,
      dsMap: Map[DataQualifierName, Set[DataCategoryName]],
      organizationId: Long
    ): Option[Iterable[String]] = {

      //p === pd qualifier <- categories
      //d === d qualifier <- categories
      // missing:
      // d.qualifier child of p.qualifier and d._2 has value that is not in some value of p._2
      //
      val privacyDataQualifier: Option[DataQualifierTree] =
        daos.dataQualifierDAO.cacheFind(organizationId, pd.dataQualifier)

      privacyDataQualifier collect { case pdq: DataQualifierTree =>
        //data qualifiers that exist in dataset that are a child of a qualifier in the privacy declaration
        dsMap
          .filter(dsm => pdq.containsChild(dsm._1))
          .flatMap((m2: (DataQualifierName, Set[DataCategoryName])) => {
            val categoriesAndAllChildrenOfDataset: Set[String] =
              m2._2.flatMap(daos.dataCategoryDAO.childrenOfInclusive(organizationId, _))
            val categoriesAndAllChildrenOfDeclaration: Set[String] =
              pd.dataCategories.flatMap(daos.dataCategoryDAO.childrenOfInclusive(organizationId, _))
            //values that are under the dataset that are not under the privacyDeclaration
            categoriesAndAllChildrenOfDataset.diff(categoriesAndAllChildrenOfDeclaration)
          })
      }
    }

    /** if we only have a dataset declaration test the dataset against the privacy declaration. */
    def datasetGamutCheck(pd: PrivacyDeclaration, ds: Dataset, mc: MessageCollector): Unit = {

      val dsPrivacyMap: Map[DataQualifierName, Set[DataCategoryName]] = ds.qualifierCategoriesMap()
      if (dsPrivacyMap.isEmpty) {
        mc.addWarning(s"The dataset ${ds.fidesKey} did not specify any privacy information")
      } else {
        gamutCheck(pd, dsPrivacyMap, ds.organizationId) match {
          case Some(i) if i.nonEmpty =>
            mc.addError(
              s"The dataset ${ds.fidesKey} contains categories [${i.mkString(",")}] under data qualifier [${dsPrivacyMap.keys.toSeq.head}] not accounted for in the privacy declaration ${pd.name}"
            )
          case _ =>
        }
      }
    }

    def datasetFieldGamutCheck(df: DatasetField, pd: PrivacyDeclaration, ds: Dataset, mc: MessageCollector): Unit = {
      val dsPrivacyMap = ds.qualifierCategoriesMapForField(df)
      if (dsPrivacyMap.isEmpty) {
        mc.addWarning(s"The dataset ${ds.fidesKey}.${df.name} did not specify any privacy information")
      } else {
        gamutCheck(pd, dsPrivacyMap, ds.organizationId) match {
          case Some(i) if i.nonEmpty =>
            mc.addError(
              s"The dataset field ${ds.fidesKey}.${df.name} contains categories [${i
                .mkString(",")}] under data qualifier [${dsPrivacyMap.keys.toSeq.head}] not accounted for in the privacy declaration ${pd.name}"
            )
          case _ =>
        }
      }
    }

    /*
      for each table[.field] spec in the privacy declaration references:
       1. does the dataset[.field] exist in eo.datasets?
       2. does it match or fall within the value in this privacy declaration?
       3. if the dataset declares a global (dataset, not field level) privacy declaration,
         and that global value does _not_ fall within this privacy declaration (but the field does,
           that is, there is no error generated so far), then we generate a warning.
     */

    //(dataset fides key, field name or "")
    val referenceTuples: Set[(String, String)] = privacyDeclaration.datasetReferences.map(splitRef)

    referenceTuples.foreach { t: (String, String) =>
      t match {
        case (a, "") =>
          datasets.get(a) match {
            case None =>
              mc.addError(s"Dataset reference $a found in declaration ${privacyDeclaration.name} was not found")
            case Some(ds) => datasetGamutCheck(privacyDeclaration, ds, mc)
          }

        case (a, b) =>
          datasets.get(a) match {
            case None =>
              mc.addError(s"Dataset reference $a found in declaration ${privacyDeclaration.name} was not found")
            case Some(ds) => ds.getField(b).foreach(datasetFieldGamutCheck(_, privacyDeclaration, ds, mc))
          }
      }

    }
  }

  /** Ensure that system does not contain a self-reference. */
  def checkSelfReference(systemObject: SystemObject, mc: MessageCollector): Unit =
    if (systemObject.systemDependencies.contains(systemObject.fidesKey)) {
      mc.addError("Invalid self reference: System cannot depend on itself")
    }

  /** Ensure that systems listed under system dependencies exist in the db. */
  def checkDependentSystemsExist(
    system: SystemObject,
    dependentSystems: Seq[SystemObject],
    mc: MessageCollector
  ): Unit =
    system.systemDependencies.diff(dependentSystems.map(_.fidesKey).toSet + system.fidesKey) collect {
      case missing if missing.nonEmpty =>
        mc.addError(s"The referenced systems [${missing.mkString(",")}] were not found.")
    }

  /** return map of approval status -> [rules that returned that rating]
    *
    * e.g (FAIL -> (policy1.rule1 -> [declarationName1, declarationName2], policy2.rule2 -> [declarationName2])
    */
  def evaluatePolicyRules(
    policies: Seq[Policy],
    system: SystemObject
  ): Map[ApprovalStatus, Map[String, Seq[String]]] = {

    val v: Seq[(Option[PolicyAction], String, String)] = for {
      d                <- system.privacyDeclarations.getOrElse(Seq())
      policy           <- policies
      rule: PolicyRule <- policy.rules.getOrElse(Set())
      action: Option[PolicyAction] = policyRuleEvaluator.matches(rule, d)
    } yield (action, policy.fidesKey + "." + rule.fidesKey, d.name)

    val collectByAction = v.collect { case (Some(rating), ruleName, declarationName) =>
      (toApprovalStatus(rating), ruleName, declarationName)
    }

    val groupByStatus = mapGrouping(collectByAction, t => t.productElement(2), Seq(0, 1))
      .asInstanceOf[Map[ApprovalStatus, Map[String, Seq[String]]]]

    //if there are any non-pass statuses, filter out the "pass" values
    if (groupByStatus.exists(_._1 != ApprovalStatus.PASS)) {
      groupByStatus.filter(_._1 != ApprovalStatus.PASS)
    } else {
      groupByStatus
    }
  }

  /** for all dependent systems, check if privacy declarations includes things that are not in the privacy set of this system.
    * Assumes that all dependent systems are populated in the dependentSystems variable
    */
  def checkDeclarationsOfDependentSystems(
    systemObject: SystemObject,
    dependentSystems: Iterable[SystemObject],
    mc: MessageCollector
  ): Unit = {
    val mergedDependencies =
      mergeDeclarations(systemObject.organizationId, systemObject.privacyDeclarations.getOrElse(Seq()))

    dependentSystems.foreach(ds => {
      val mergedDependenciesForDs =
        mergeDeclarations(systemObject.organizationId, ds.privacyDeclarations.getOrElse(Seq()))
      val diff = diffDeclarations(systemObject.organizationId, mergedDependenciesForDs, mergedDependencies)
      if (diff.nonEmpty) {
        mc.addWarning(
          s"The system ${ds.fidesKey} includes privacy declarations that do not exist in ${systemObject.fidesKey} : ${diff.map(_.name).mkString(",")}"
        )
      }
    })
  }

  def evaluateSystem(fidesKey: String, eo: EvaluationObjectSet): SystemEvaluation = {
    val mc     = new MessageCollector()
    val system = eo.systems(fidesKey) //TODO err on missing

    val m: Map[ApprovalStatus, Map[String, Seq[String]]] = evaluatePolicyRules(eo.policies, system)
    val dependentSystems                                 = system.systemDependencies.map(eo.systems.get).filter(_.nonEmpty).map(_.get)
    //val warnings                                         = Seq() //checkDeclarationsOfDependentSystems(system, dependentSystems)
    // val errors =
    checkDependentSystemsExist(system, dependentSystems.toSeq, mc)
    checkDeclarationsOfDependentSystems(system, dependentSystems.toSeq, mc)
    checkSelfReference(system, mc)
    system.privacyDeclarations.foreach(pds => pds.foreach(checkPrivacyDeclaration(_, eo.datasets, mc)))
    val overallApproval = {
      if (mc.hasErrors) {
        ApprovalStatus.ERROR
      } else if (m.contains(ApprovalStatus.FAIL)) {
        ApprovalStatus.FAIL
      } else if (m.contains(ApprovalStatus.MANUAL)) {
        ApprovalStatus.MANUAL
      } else {
        ApprovalStatus.PASS
      }
    }

    SystemEvaluation(m, mc.warnings.toSeq, mc.errors.toSeq, overallApproval)
  }

  // ------------------  support functions ------------------

  private def toApprovalStatus(action: PolicyAction): ApprovalStatus =
    action match {
      case PolicyAction.ACCEPT  => ApprovalStatus.PASS
      case PolicyAction.REJECT  => ApprovalStatus.FAIL
      case PolicyAction.REQUIRE => ApprovalStatus.MANUAL
    }
  /** For all declarations
    *  - match:
    *    - they have the same data use
    *    - they have the same data qualifier
    *
    * data subjects are the mergeDeclarations of both data subjects
    * data categories are the mergeDeclarations of both data categories
    *
    * where "mergeDeclarations" means:
    *      - mergeAndReduce both sets of values
    *      - reduce both sets of values using TreeCache mergeAndReduce
    *
    * Return a sequence of [{set of declaration names that were used to generate this merge}, merged declaration}]
    * Merged set does not retain field information.
    */

  def mergeDeclarations(organizationId: Long, declarations: Iterable[PrivacyDeclaration]): Set[PrivacyDeclaration] = {
    declarations
      .groupBy(d => (d.dataQualifier, d.dataUse))
      .map { t: ((DataQualifierName, DataUseName), Iterable[PrivacyDeclaration]) =>
        val categories = daos.dataCategoryDAO.mergeAndReduce(organizationId, t._2.flatMap(_.dataCategories).toSet)
        val subjectCategories =
          daos.dataSubjectDAO.mergeAndReduce(organizationId, t._2.flatMap(_.dataSubjects).toSet)
        PrivacyDeclaration(
          0L,
          0L,
          t._2.map(_.name).toSet.mkString(","),
          categories,
          t._1._2,
          t._1._1,
          subjectCategories,
          Set()
        )
      }
      .toSet
  }

  /** PrivacyDeclaration diff generated by comparing values held in declaration sets a,b, where each combination
    * of (DataQualifier,DataUse) is considered unique. This means grouping and merging category and subject
    * category combinations under each key.
    *
    * Diff does not retain privacy information
    */
  def diffDeclarations(
    organizationId: Long,
    a: Iterable[PrivacyDeclaration],
    b: Iterable[PrivacyDeclaration]
  ): Set[PrivacyDeclaration] = {

    val l = mergeDeclarations(organizationId, a)
    val r = mergeDeclarations(organizationId, b)

    val rGrouped: Map[(DataQualifierName, DataUseName), Set[PrivacyDeclaration]] =
      r.groupBy(d => (d.dataQualifier, d.dataUse))
    val lGrouped: Map[(DataQualifierName, DataUseName), Set[PrivacyDeclaration]] =
      l.groupBy(d => (d.dataQualifier, d.dataUse))

    val grouped: Set[PrivacyDeclaration] = lGrouped.map {
      t: ((DataQualifierName, DataUseName), Set[PrivacyDeclaration]) =>
        val rVals: Set[PrivacyDeclaration] = rGrouped.getOrElse(t._1, Set())
        val rCategories                    = rVals.flatMap(_.dataCategories)
        val rSubjectCategories             = rVals.flatMap(_.dataSubjects)

        val lCategories        = t._2.flatMap(_.dataCategories)
        val lSubjectCategories = t._2.flatMap(_.dataSubjects)

        val categoryDiff = daos.dataCategoryDAO.diff(organizationId, rCategories, lCategories)
        val subjectCategoryDiff =
          daos.dataSubjectDAO.diff(organizationId, rSubjectCategories, lSubjectCategories)

        PrivacyDeclaration(
          0L,
          0L,
          t._2.map(_.name).mkString(","),
          categoryDiff,
          t._1._2,
          t._1._1,
          subjectCategoryDiff,
          Set()
        )
    }.toSet

    grouped.filter(d => d.dataCategories.nonEmpty || d.dataSubjects.nonEmpty)
  }
}
