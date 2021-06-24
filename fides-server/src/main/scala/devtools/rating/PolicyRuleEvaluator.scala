package devtools.rating

import com.typesafe.scalalogging.LazyLogging
import devtools.domain._
import devtools.domain.definition.TreeItem
import devtools.domain.enums._
import devtools.domain.policy.{Declaration, PolicyRule}
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.DAOs
import devtools.util.TreeCache

class PolicyRuleEvaluator(val daos: DAOs) extends LazyLogging {

  // ------------------  checks by taxonomy type ------------------
  /** Categories matches the policy rule category value(s) */
  def categoriesMatch(organizationId: Long, categories: PolicyValueGrouping, declaration: Declaration): Boolean = {
    groupingMatch("categories", organizationId, daos.dataCategoryDAO, categories, declaration.dataCategories)

  }

  /** Use matches the policy rule uses value */
  def usesMatch(organizationId: Long, uses: PolicyValueGrouping, declaration: Declaration): Boolean = {
    groupingMatch("data uses", organizationId, daos.dataUseDAO, uses, Set(declaration.dataUse))
  }

  /** Subject categories matches the policy rule subject category value(s) */
  def subjectCategoriesMatch(
    organizationId: Long,
    subjectCategories: PolicyValueGrouping,
    declaration: Declaration
  ): Boolean = {
    groupingMatch(
      "data subject categories",
      organizationId,
      daos.dataSubjectCategoryDAO,
      subjectCategories,
      declaration.dataSubjectCategories
    )
  }

  /** Qualifier matches the policy rule qualifier value */
  def qualifierMatches(
    organizationId: Long,
    qualifier: Option[DataQualifierName],
    declaration: Declaration
  ): Boolean = {
    //an empty dataQualifier will always match, as it's "unqualified data"
    qualifier match {
      case None => true
      case Some(q) =>
        daos.dataQualifierDAO.cacheFind(organizationId, q) match {
          case None       => throw InvalidDataException(s"No dataQualifier found for the fidesKey(s) $q")
          case Some(tree) => tree.exists(_.fidesKey == declaration.dataQualifier)
        }
    }
  }

  /** return Some(action) for a matching rule, or None if the rule does not match */
  def matches(rule: PolicyRule, declaration: Declaration): Option[PolicyAction] = {
    val c = categoriesMatch(rule.organizationId, rule.dataCategories, declaration)
    val u = usesMatch(rule.organizationId, rule.dataUses, declaration)
    val q = qualifierMatches(rule.organizationId, rule.dataQualifier, declaration)
    val s = subjectCategoriesMatch(rule.organizationId, rule.dataSubjectCategories, declaration)

    if (c && u && q && s) {
      logger.debug("matching on rule={}, declaration={}", rule, declaration)
      Some(rule.action)
    } else {
      None
    }
  }

  // ------------------  support functions ------------------


  /** True iff the child key can be found in the input set or children (including root values). */
  private def isChild(tree: TreeItem[_, _], possibleChildKey: String): Boolean = {
    tree.exists { t: TreeItem[_, _] => t.fidesKey == possibleChildKey }
  }

  private def inclusionMatches(inclusion: RuleInclusion, booleans: Set[Boolean]): Boolean = {
    val ctTrue = booleans.count(_ == true)
    val size   = booleans.size
    if (size == 0) {
      false
    } else {
      inclusion match {
        case RuleInclusion.ALL  => ctTrue == size
        case RuleInclusion.ANY  => ctTrue > 0
        case RuleInclusion.NONE => ctTrue == 0
      }
    }
  }

  /** Return an error message for types that have no corresponding entry in the cache */
  private def checkForMissingValues(
    organizationId: Long,
    typeKey: String,
    values: Set[String],
    cache: TreeCache[_, _]
  ): Unit = {
    val missing = values.filterNot(cache.containsFidesKey(organizationId, _))
    if (missing.nonEmpty) {
      throw InvalidDataException(s"No $typeKey values found with fides keys [${missing.mkString(",")}]")
    }
  }


  def groupingMatch[T <: TreeItem[T, Long]](
    label: String,
    organizationId: Long,
    cache: TreeCache[T, _],
    policyGrouping: PolicyValueGrouping,
    declarationValues: Set[String]
  ): Boolean = {

    def isChildOf(trees: Set[TreeItem[_, _]], possibleChildKey: String): Set[Boolean] = {
      trees.map { isChild(_, possibleChildKey) }
    }

    checkForMissingValues(organizationId, s"declaration $label", declarationValues, cache)
    checkForMissingValues(organizationId, s"policy rule $label", policyGrouping.values, cache)

    val trees = policyGrouping.values.map(v => (v, cache.cacheFind(organizationId, v)))
    //output result for the application to each declaration
    val booleanMatches: Set[Boolean] =
      declarationValues.flatMap(d => isChildOf(trees.map { t => t._2.get }, d))
    inclusionMatches(policyGrouping.inclusion, booleanMatches)
  }

}
