package devtools.rating

import devtools.Generators._
import devtools.domain.definition.WithFidesKey
import devtools.domain.enums.PolicyAction.REJECT
import devtools.domain.enums.PolicyValueGrouping
import devtools.domain.enums.RuleInclusion.{ALL, ANY}
import devtools.domain.policy.Policy
import devtools.domain.{Dataset, PrivacyDeclaration, Registry, SystemObject}
import devtools.util.waitFor
import devtools.{App, TestUtils}
class RatingTestData extends TestUtils {

  val runKey: String             = fidesKey
  def wRunKey(s: String): String = s"$s-$runKey"
  // -----------------------------------------
  //            policy rules
  // -----------------------------------------

  /* Some sample rules */
  private val rule1 =
    policyRuleOf(
      //category
      PolicyValueGrouping(ANY, Set("customer_content_data")),
      //use
      PolicyValueGrouping(ANY, Set("market_advertise_or_promote")),
      //dataQualifier
      "pseudonymized_data",
      PolicyValueGrouping(ANY, Set("customer")),
      REJECT,
      "any identified customer data for advertising"
    )

  //any identified data, just identified using roots
  private val rule2 =
    policyRuleOf(
      //category
      PolicyValueGrouping(
        ANY,
        Set("customer_content_data", "cloud_service_provider_data", "derived_data", "account_data")
      ),
      //use
      PolicyValueGrouping(
        ANY,
        Set(
          "personalize",
          "share",
          "provide",
          "offer_upgrades_or_upsell",
          "train_ai_system",
          "collect",
          "market_advertise_or_promote",
          "improve"
        )
      ),
      //dataQualifier
      "identified_data",
      PolicyValueGrouping(ANY, availableDataSubjects.toSet),
      REJECT,
      "any identified data"
    )

  //disallow collecting identified account data for patients
  private val rule3 =
    policyRuleOf(
      //category
      PolicyValueGrouping(
        ANY,
        Set("customer_content_data", "cloud_service_provider_data", "derived_data", "account_data")
      ),
      //use
      PolicyValueGrouping(ANY, Set("collect")),
      //dataQualifier
      "identified_data",
      PolicyValueGrouping(ANY, Set("patient")),
      REJECT,
      "accept any aggregated data"
    )

  //disallow collecting identified account data for customers in combination with financial data
  private val rule4 = policyRuleOf(
    //category
    PolicyValueGrouping(ALL, Set("account_data", "financial_details")),
    //use
    PolicyValueGrouping(ANY, Set("collect")),
    //dataQualifier
    "pseudonymized_data",
    PolicyValueGrouping(ANY, Set("customer")),
    REJECT,
    "rule4"
  )

  // -----------------------------------------
  //            Policies
  // -----------------------------------------
  private val policy1 = policyOf(wRunKey("policy1"), rule1, rule2)
  private val policy2 = policyOf(wRunKey("policy2"), rule3, rule4)
  // -----------------------------------------
  //            Datasets
  // -----------------------------------------

  private val ds1Key = wRunKey("d1").replace(".", "_")
  private val dataset1 = datasetOf(
    ds1Key,
    datasetFieldOf("d1f1", "unlinked_pseudonymized_data", Set("personal_genetic_data", "personal_biometric_data")), //r1
    datasetFieldOf("d1f2", "identified_data", Set("telemetry_data")),                                               //r2
    datasetFieldOf("d1f3", "identified_data", Set("operations_data"))
  ) //r3
  private val ds2Key = wRunKey("d2").replace(".", "_")
  private val dataset2 = datasetOf(
    ds2Key,
    datasetFieldOf("d2f2", "pseudonymized_data", Set("account_data", "financial_details")), //r4
    datasetFieldOf("d2f3", "aggregated_data", Set("demographic_information"))
  ) //safe

  // -----------------------------------------
  //            Declarations
  // -----------------------------------------
  private val depFailure = PrivacyDeclaration(
    0L,
    0L,
    "sensitiveData",
    Set("customer_content_data", "cloud_service_provider_data", "derived_data", "account_data"),
    "collect",
    "identified_data",
    Set("customer"),
    Set(s"$ds1Key.d1f3")
  )

  //r1 categories. all other values match
  private val depMatchesOnlyR1 =
    PrivacyDeclaration(0L, 0L, "test1", Set("credentials"), "provide", "identified_data", Set("prospect"), Set(ds1Key))

  private val depMatchesOnlyR2 =
    PrivacyDeclaration(
      0L,
      0L,
      "identified end-user data for prospecting",
      Set("telemetry_data", "connectivity_data"),
      "share",
      "identified_data",
      Set("prospect"),
      Set(s"$ds1Key.d1f2")
    )

  private val depMatchesOnlyR3 = PrivacyDeclaration(
    0L,
    0L,
    "identified account data for prospecting",
    Set("payment_instrument_data", "account_or_administration_contact_information"),
    "improvement_of_business_support_for_contracted_service",
    "identified_data",
    Set("prospect"),
    Set(s"$ds1Key.d1f3")
  )

  private val depMatchesOnlyR4 =
    PrivacyDeclaration(
      0L,
      0L,
      "identified credentials for providing",
      Set("credentials"),
      "provide",
      "identified_data",
      Set("trainee"),
      Set(s"$ds2Key", s"$ds2Key.d2f2")
    )

  private val depMatchesBothR1R2 =
    PrivacyDeclaration(
      0L,
      0L,
      "operations data for improvement",
      Set("operations_data"),
      "improve",
      "identified_data",
      Set("prospect", "employee", "trainee"),
      Set(s"$ds2Key.d2f2", s"$ds2Key.d2f3")
    )

  // -----------------------------------------
  //            Systems
  // -----------------------------------------

  val system1: SystemObject =
    systemOf(wRunKey("system1"), depMatchesOnlyR1, depMatchesOnlyR2, depMatchesOnlyR3).copy(systemDependencies = Set())
  val system2: SystemObject = systemOf(wRunKey("system2"), depMatchesBothR1R2, depMatchesOnlyR4)
    .copy(systemDependencies = Set(wRunKey("system3")))
  val system3: SystemObject =
    systemOf(wRunKey("system3"), depFailure).copy(systemDependencies = Set(wRunKey("system2")))

  // -----------------------------------------
  //            Registries
  // -----------------------------------------
  private val registrySvc = App.registryService
  private val systemSvc   = App.systemService
  private val datasetSvc  = App.datasetService
  private val policySvc   = App.policyService

  private def toMap[T <: WithFidesKey[_, _]](ts: T*): Map[String, T] = ts.map(t => t.fidesKey -> t).toMap
  val d1: Dataset = waitFor(
    datasetSvc.create(dataset1, requestContext).flatMap(d => datasetSvc.findById(d.id, requestContext))
  ).get
  val d2: Dataset = waitFor(
    datasetSvc.create(dataset2, requestContext).flatMap(d => datasetSvc.findById(d.id, requestContext))
  ).get
  val p1: Policy = waitFor(
    policySvc.create(policy1, requestContext).flatMap(p => policySvc.findById(p.id, requestContext))
  ).get
  val p2: Policy = waitFor(
    policySvc.create(policy2, requestContext).flatMap(p => policySvc.findById(p.id, requestContext))
  ).get
  val s1: SystemObject = waitFor(
    systemSvc.create(system1, requestContext).flatMap(r => systemSvc.findById(r.id, requestContext))
  ).get
  val s2: SystemObject = waitFor(
    systemSvc.create(system2, requestContext).flatMap(r => systemSvc.findById(r.id, requestContext))
  ).get
  val s3: SystemObject = waitFor(
    systemSvc.create(system3, requestContext).flatMap(r => systemSvc.findById(r.id, requestContext))
  ).get
  private val registry1 =
    Registry(
      0,
      1,
      wRunKey("registry1"),
      None,
      None,
      None,
      None,
      Some(Left(Seq(s1.id, s2.id, s3.id))),
      None,
      None
    )
  val r1: Registry = waitFor(
    registrySvc.create(registry1, requestContext).flatMap(r => registrySvc.findById(r.id, requestContext))
  ).get

  val systems: Map[String, SystemObject] = toMap(s1, s2)
  val datasets: Map[String, Dataset]     = toMap(d1, d2)
  val policies: Map[String, Policy]      = toMap(p1, p2)
  val registries: Map[String, Registry]  = toMap(r1)

  def destroy(): Unit = {
    systems.values.foreach(v => datasetSvc.dao.delete(v.id))
    datasets.values.foreach(v => datasetSvc.dao.delete(v.id))
    policies.values.foreach(v => policySvc.dao.delete(v.id))
    registries.values.foreach(v => registrySvc.dao.delete(v.id))
  }

}
