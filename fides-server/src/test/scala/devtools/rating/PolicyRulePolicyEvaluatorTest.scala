package devtools.rating

import devtools.domain.enums.PolicyValueGrouping
import devtools.domain.enums.RuleInclusion.{ALL, ANY, NONE}
import devtools.domain.policy.Declaration
import devtools.{App, TestUtils}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class PolicyRulePolicyEvaluatorTest extends AnyFunSuite with TestUtils with BeforeAndAfterAll {

  val rater: PolicyRuleEvaluator = App.policyRuleEvaluator

  //categories
  val p1   = "customer_content_data"
  val p1c1 = "credentials"
  val p1c2 = "personal_genetic_data"
  val p2   = "derived_data"
  val p2c1 = "end_user_identifiable_information"
  val p2c2 = "users_environmental_sensor_data"

  test("test category match") {
    rater.categoriesMatch(
      1,
      PolicyValueGrouping(ANY, Set(p1)),
      Declaration(Set(p1), null, null, null)
    ) shouldEqual true
    rater.categoriesMatch(
      1,
      PolicyValueGrouping(ALL, Set(p1)),
      Declaration(Set(p1c1, p1c2, p1), null, null, null)
    ) shouldEqual true
    rater.categoriesMatch(
      1,
      PolicyValueGrouping(ANY, Set(p1)),
      Declaration(Set(p1, p2), null, null, null)
    ) shouldEqual true
    rater.categoriesMatch(
      1,
      PolicyValueGrouping(ALL, Set(p1)),
      Declaration(Set(p1, p2), null, null, null)
    ) shouldEqual false
    rater.categoriesMatch(
      1,
      PolicyValueGrouping(NONE, Set(p1)),
      Declaration(Set(p2, p2c1, p2c2), null, null, null)
    ) shouldEqual true
  }

  //uses
  val u1   = "provide"
  val u1c1 = "provide_operational_support_for_contracted_service"
  val u1c2 = "improvement_of_business_support_for_contracted_service"
  val u2   = "market_advertise_or_promote"
  val u2c1 = "promote_based_on_contextual_information"
  test("test uses match") {
    rater.usesMatch(1, PolicyValueGrouping(ANY, Set(u1)), Declaration(null, u1, null, null)) shouldEqual true
    rater.usesMatch(1, PolicyValueGrouping(ANY, Set(u1, u2)), Declaration(null, u2, null, null)) shouldEqual true
    rater.usesMatch(
      1,
      PolicyValueGrouping(NONE, Set(u1c1, u1c2)),
      Declaration(null, u1c1, null, null)
    ) shouldEqual false
    rater.usesMatch(
      1,
      PolicyValueGrouping(NONE, Set(u1c1, u1c2)),
      Declaration(null, u2, null, null)
    ) shouldEqual true
  }
  //qualifiers
  val q1     = "aggregated_data"
  val q1c1   = "anonymized_data"
  val q1c1c1 = "identified_data"
  test("test qualifiers") {
    rater.qualifierMatches(1, Some(q1), Declaration(null, null, q1, null)) shouldEqual true
    rater.qualifierMatches(1, Some(q1), Declaration(null, null, q1c1, null)) shouldEqual true
    rater.qualifierMatches(1, Some(q1c1), Declaration(null, null, q1c1c1, null)) shouldEqual true
    rater.qualifierMatches(1, None, Declaration(null, null, q1, null)) shouldEqual true
  }

  //subject categories
  val s1 = "anonymous_user"
  val s2 = "citizen_voter"
  val s3 = "commuter"
  test("test subject category match") {
    rater.subjectCategoriesMatch(
      1,
      PolicyValueGrouping(ANY, Set(s1)),
      Declaration(null, null, null, Set(s1))
    ) shouldEqual true
    rater.subjectCategoriesMatch(
      1,
      PolicyValueGrouping(ANY, Set(s1, s2)),
      Declaration(null, null, null, Set(s1))
    ) shouldEqual true
    rater.subjectCategoriesMatch(
      1,
      PolicyValueGrouping(NONE, Set(s1, s2)),
      Declaration(null, null, null, Set(s3))
    ) shouldEqual true
    rater.subjectCategoriesMatch(
      1,
      PolicyValueGrouping(NONE, Set(s1, s2)),
      Declaration(null, null, null, Set(s1))
    ) shouldEqual false

  }

}
