package devtools.rating

import devtools.Generators._
import devtools.domain.definition.WithFidesKey
import devtools.domain.enums.PolicyAction.REJECT
import devtools.domain.enums.PolicyValueGrouping
import devtools.domain.enums.RuleInclusion.ANY
import devtools.domain.policy.{PrivacyDeclaration, Policy}
import devtools.domain.{Dataset, Registry, SystemObject}
import devtools.util.waitFor
import devtools.{App, TestUtils}

import scala.concurrent.ExecutionContext
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
      PolicyValueGrouping(ANY, availableDataCategories.toSet),
      //use
      PolicyValueGrouping(ANY, availableDataUses.toSet),
      //dataQualifier
      "pseudonymized_data",
      PolicyValueGrouping(ANY, availableDataSubjects.toSet),
      REJECT,
      "rule1"
    )

  private val rule2 =
    policyRuleOf(
      //category
      PolicyValueGrouping(ANY, availableDataCategories.toSet),
      //use
      PolicyValueGrouping(ANY, availableDataUses.toSet),
      //dataQualifier
      "pseudonymized_data",
      PolicyValueGrouping(ANY, availableDataSubjects.toSet),
      REJECT,
      "rule2"
    )
  private val rule3 =
    policyRuleOf(
      //category
      PolicyValueGrouping(ANY, availableDataCategories.toSet),
      //use
      PolicyValueGrouping(ANY, availableDataUses.toSet),
      //dataQualifier
      "pseudonymized_data",
      PolicyValueGrouping(ANY, availableDataSubjects.toSet),
      REJECT,
      "rule3"
    )

  private val rule4 = policyRuleOf(
    //category
    PolicyValueGrouping(ANY, availableDataCategories.toSet),
    //use
    PolicyValueGrouping(ANY, availableDataUses.toSet),
    //dataQualifier
    "pseudonymized_data",
    PolicyValueGrouping(ANY, availableDataSubjects.toSet),
    REJECT,
    "rule4"
  )

  // -----------------------------------------
  //            Policies
  // -----------------------------------------
  private val policy1 = policyOf(wRunKey("policy1"), rule1, rule2)
  private val policy2 = policyOf(wRunKey("policy2"), rule3, rule4)
  // -----------------------------------------
  //            Declarations
  // -----------------------------------------
  //r1 categories. all other values match
  private val depMatchesOnlyR1 =
    PrivacyDeclaration("test1", Set("credentials"), "provide", "identified_data", Set("prospect"), Set())

  private val depMatchesOnlyR2 =
    PrivacyDeclaration(
      "test2",
      Set("telemetry_data", "connectivity_data"),
      "share",
      "identified_data",
      Set("prospect"),
      Set()
    )

  private val depMatchesOnlyR3 = PrivacyDeclaration(
    "test3",
    Set("payment_instrument_data", "account_or_administration_contact_information"),
    "improvement_of_business_support_for_contracted_service",
    "identified_data",
    Set("prospect"),
    Set()
  )

  private val depMatchesOnlyR4 =
    PrivacyDeclaration("test4", Set("credentials"), "provide", "identified_data", Set("trainee"), Set())

  private val depMatchesBothR1R2 =
    PrivacyDeclaration(
      "test5",
      Set("operations_data"),
      "improve",
      "identified_data",
      Set("prospect", "employee", "trainee"),
      Set()
    )

  // -----------------------------------------
  //            Datasets
  // -----------------------------------------
  private val fullyPopulatedField = datasetFieldOf("all")
    .copy(dataCategories = Some(availableDataCategories.toSet), dataQualifier = Some("identified_data"))
  private val dataset1 = datasetOf(wRunKey("d1"))
  //,
  //  datasetFieldOf("t1f1"), datasetFieldOf("t1f2"), datasetFieldOf("t1f3"))
  //  datasetTableOf("d1t2", datasetFieldOf("t2f1"), datasetFieldOf("t2f2"), datasetFieldOf("t2f3"))

  private val dataset2 = datasetOf(wRunKey("d2"))

  //, datasetTableOf("d2t3", datasetFieldOf("t3f1"), datasetFieldOf("t3f2"), datasetFieldOf("t3f3")),
  // datasetTableOf("d2t4", datasetFieldOf("t4f1"), datasetFieldOf("t4f2"), datasetFieldOf("t4f3"))
  //)

  // -----------------------------------------
  //            Systems
  // -----------------------------------------

  val system1: SystemObject =
    systemOf(wRunKey("system1"), depMatchesOnlyR1, depMatchesOnlyR2, depMatchesOnlyR3)
  val system2: SystemObject = systemOf(wRunKey("system2"), depMatchesBothR1R2, depMatchesOnlyR4)
    .copy(systemDependencies = Set(wRunKey("system3")))
  val system3: SystemObject = systemOf(wRunKey("system3")).copy(
    systemDependencies = Set(wRunKey("system2"), wRunKey("system3"))
  )

  // -----------------------------------------
  //            Registries
  // -----------------------------------------
  private val registrySvc = App.registryService
  private val systemSvc   = App.systemService
  private val datasetSvc  = App.datasetService
  private val policySvc   = App.policyService
  private val registry1 =
    Registry(
      0,
      1,
      wRunKey("registry1"),
      None,
      None,
      None,
      None,
      Some(Right(Seq(system1, system2, system3))),
      None,
      None
    )

  private def toMap[T <: WithFidesKey[_, _]](ts: T*): Map[String, T] = ts.map(t => t.fidesKey -> t).toMap
  implicit val executionContext: ExecutionContext                    = App.executionContext
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
