package devtools.rating

import devtools.Generators.SystemObjectGen
import devtools.domain.{Dataset, PrivacyDeclaration}
import devtools.domain.enums.ApprovalStatus
import devtools.util.waitFor
import devtools.validation.MessageCollector
import devtools.{App, TestUtils}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.concurrent.ExecutionContext
class SystemEvaluatorTest extends AnyFunSuite with TestUtils {

  implicit val context: ExecutionContext = App.executionContext
  private val systemEvaluator            = new SystemEvaluator(App.daos)
  private val evaluator                  = new Evaluator(App.daos)

  test("test rate rating catch missing system dependency") {
    //for this test we need to set the privacyDeclarations to "Some" since if the system is
    //understood to be not hydrated we will try to retrieve the value from the db, which
    //will fail for this test value.
    val sys = SystemObjectGen.sample.get
      .copy(fidesKey = "a", privacyDeclarations = Some(Seq()), systemDependencies = Set("missing1", "missing2"))
    val eo                  = waitFor(evaluator.retrievePopulated(Seq(sys)))
    val v: SystemEvaluation = systemEvaluator.evaluateSystem(sys.fidesKey, eo)

    v.errors should containMatchString(
      "The referenced systems \\[.*\\] were not found."
    )

    v.overallApproval shouldEqual ApprovalStatus.ERROR
  }

  test("test self reference") {
    val sys =
      SystemObjectGen.sample.get.copy(fidesKey = "a", privacyDeclarations = Some(Seq()), systemDependencies = Set("a"))
    val eo                  = waitFor(evaluator.retrievePopulated(Seq(sys)))
    val v: SystemEvaluation = systemEvaluator.evaluateSystem(sys.fidesKey, eo)

    v.errors should containMatchString(
      "Invalid self reference"
    )
    v.overallApproval shouldEqual ApprovalStatus.ERROR
  }

  //categories
  private def cat_root1        = "customer_content_data"
  private def cat_root1_child1 = "credentials"
  private def cat_root2        = "derived_data"

  //subject categories
  private def scat_root1 = "customer"
  private def scat_root2 = "patient"

  //qualifiers
  private def q_root = "aggregated_data"

  //use
  private def use_root1 = "share"
  private def use_root2 = "personalize"
  test("test system declaration dependencies") {

    def testDependencies(parent: Seq[PrivacyDeclaration], children: Seq[PrivacyDeclaration]): Seq[String] = {
      val s1 = systemOf("a").copy(systemDependencies = Set("b"), privacyDeclarations = Some(parent))
      val s2 = systemOf("b").copy(privacyDeclarations = Some(children))
      val mc = new MessageCollector()
      systemEvaluator.checkDeclarationsOfDependentSystems(s1, Seq(s2), mc)
      mc.warnings.toSeq
    }

    //Just different category
    testDependencies(
      Seq(PrivacyDeclaration(0L, 0L, "test2", Set(cat_root1), use_root1, q_root, Set(scat_root1), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "test3", Set(cat_root2), use_root1, q_root, Set(scat_root1), Set()))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //Just different subject category
    testDependencies(
      Seq(PrivacyDeclaration(0L, 0L, "test4", Set(cat_root1), use_root1, q_root, Set(scat_root1), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "test5", Set(cat_root1), use_root1, q_root, Set(scat_root2), Set()))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //child with child cat, same qualifier/use is ok

    testDependencies(
      Seq(PrivacyDeclaration(0L, 0L, "test6", Set(cat_root1), use_root1, q_root, Set(scat_root1), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "test7", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1), Set()))
    ).size shouldEqual 0

    //child with parent cat, same qualifier/use -> message

    testDependencies(
      Seq(PrivacyDeclaration(0L, 0L, "test8", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "test9", Set(cat_root1), use_root1, q_root, Set(scat_root1), Set()))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //child with NEW (qualifier/use) pair
    testDependencies(
      Seq(PrivacyDeclaration(0L, 0L, "test10", Set(cat_root1), use_root1, q_root, Set(scat_root1), Set())),
      Seq(
        PrivacyDeclaration(0L, 0L, "test11", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1), Set()),
        PrivacyDeclaration(0L, 0L, "test12", Set(cat_root2), use_root2, q_root, Set(scat_root1), Set())
      )
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

  }

  test("test privacy-declaration vs dataset privacy declaration") {

    def testPrivacyDeclaration(
      privacyDeclaration: PrivacyDeclaration,
      dataset: Dataset,
      returnWarnings: Boolean = false
    ): Seq[String] = {
      val mc = new MessageCollector
      systemEvaluator.checkPrivacyDeclaration(privacyDeclaration, Map(dataset.fidesKey -> dataset), mc)

      if (returnWarnings) mc.warnings.toSeq else mc.errors.toSeq
    }

    val pd = PrivacyDeclaration(0L, 0L, "a", Set(), "aggregated_data", "share", Set(), Set())

//    "aggregated_data": {
//      "anonymized_data": {
//      "unlinked_pseudonymized_data": {
//      "pseudonymized_data": {

    //categories:
//    "cloud_service_provider_data": [
//    "access_and_authentication_data",
//    "operations_data"
//    ],
//    "derived_data": [
//    {
//      "end_user_identifiable_information": [
//      // derived data associated with a user that is captured or generated from the use of the service by that user
//      "telemetry_data",
//      "connectivity_data",

    //1. dataset or field doesn't exist

    testPrivacyDeclaration(pd.copy(datasetReferences = Set("b")), datasetOf(None, None)) should containMatchString(
      "Dataset reference b found in declaration a was not found"
    )
    //2. dataset category doesn't match privacy; literal match

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("credentials"), datasetReferences = Set("a")),
      datasetOf(Some("aggregated_data"), Some(Set("operations_data")))
    ) should containMatchString(
      "The dataset a contains categories \\[operations_data\\] under data qualifier \\[aggregated_data\\]"
    )
    //3. dataset qualifier doesn't match privacy; literal match

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("credentials"), datasetReferences = Set("a")),
      datasetOf(Some("identified_data"), Some(Set("operations_data")))
    ) should containMatchString(
      "The dataset a contains categories \\[operations_data\\] under data qualifier \\[identified_data\\]"
    )
    //4. dataset category contains a child of one of the privacy declaration values is fine:
    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(Some("aggregated_data"), Some(Set("end_user_identifiable_information")))
    ) shouldBe Seq()

    //5. dataset category contains grandchild is ok:

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(Some("aggregated_data"), Some(Set("profiling_data")))
    ) shouldBe Seq()

    //5. dataset qualifier contains child
    testPrivacyDeclaration(
      pd.copy(dataQualifier = "identified_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(Some("aggregated_data"), Some(Set("derived_data")))
    ) shouldBe Seq()
    //6. dataset.field doesn't match privacy

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("credentials"), datasetReferences = Set("a.a")),
      datasetOf(None, None, datasetFieldOf(Some("aggregated_data"), Some(Set("operations_data"))))
    ) should containMatchString(
      "The dataset field a.a contains categories \\[operations_data\\] under data qualifier \\[aggregated_data\\]"
    )

    //7. dataset category doesn't match privacy; literal match
    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("credentials"), datasetReferences = Set("a.a")),
      datasetOf(None, None, datasetFieldOf(Some("identified_data"), Some(Set("access_and_authentication_data"))))
    ) should containMatchString(
      "The dataset field a.a contains categories \\[access_and_authentication_data\\] under data qualifier \\[identified_data\\]"
    )
    //8. qualifier doesn't match privacy; literal match

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("credentials"), datasetReferences = Set("a.a")),
      datasetOf(None, None, datasetFieldOf(Some("identified_data"), Some(Set("access_and_authentication_data"))))
    ) should containMatchString(
      "The dataset field a.a contains categories \\[access_and_authentication_data\\] under data qualifier \\[identified_data\\]"
    )
    //9. child values:
    // dataset category contains a child of one of the privacy declaration values;

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(None, None, datasetFieldOf(Some("aggregated_data"), Some(Set("end_user_identifiable_information"))))
    ) shouldBe Seq()

    //10. dataset category contains grandchild

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(None, None, datasetFieldOf(Some("aggregated_data"), Some(Set("profiling_data"))))
    ) shouldBe Seq()

    //11. dataset qualifier contains child

    testPrivacyDeclaration(
      pd.copy(dataQualifier = "identified_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(None, None, datasetFieldOf(Some("aggregated_data"), Some(Set("derived_data"))))
    ) shouldBe Seq()

    //12. no privacy gamut found for dataset or field
    testPrivacyDeclaration(
      pd.copy(dataQualifier = "aggregated_data", dataCategories = Set("derived_data"), datasetReferences = Set("a")),
      datasetOf(None, None),
      true
    ) should containMatchString("The dataset a did not specify any privacy information")

  }
  test("test merge declarations") {
    def merge(declarations: PrivacyDeclaration*) = systemEvaluator.mergeDeclarations(3L, declarations)

    //merge identical elements should return same element
    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca", "ca1"), "ua", "qa", Set("sa", "sa1"), Set()),
      PrivacyDeclaration(0L, 0L, "a", Set("ca", "ca1"), "ua", "qa", Set("sa", "sa1"), Set()),
      PrivacyDeclaration(0L, 0L, "a", Set("ca", "ca1"), "ua", "qa", Set("sa", "sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set()))
    //same split into 2 declarations
    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca1"), "ua", "qa", Set("sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a,b", Set("ca"), "ua", "qa", Set("sa"), Set()))

    //merge elements in a single declaration
    merge(PrivacyDeclaration(0L, 0L, "a", Set("ca", "ca1"), "ua", "qa", Set("sa", "sa1"), Set())) shouldBe Set(
      PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())
    )
    //same split into 2 declarations
    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca1"), "ua", "qa", Set("sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a,b", Set("ca"), "ua", "qa", Set("sa"), Set()))

    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua", "qa", Set("sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a,b", Set("ca"), "ua", "qa", Set("sa"), Set()))

    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua", "qa", Set("sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a,b", Set("ca"), "ua", "qa", Set("sa"), Set()))

    //different use values
    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua", "qa", Set("sa1"), Set()),
      PrivacyDeclaration(0L, 0L, "c", Set("ca1"), "ub", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "d", Set("ca2"), "ub", "qa", Set("sa1"), Set())
    ) shouldBe Set(
      PrivacyDeclaration(0L, 0L, "a,b", Set("ca"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "c,d", Set("ca"), "ub", "qa", Set("sa"), Set())
    )

    //same use values, different category roots
    merge(
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua", "qa", Set("sa1"), Set()),
      PrivacyDeclaration(0L, 0L, "c", Set("cb1"), "ua", "qa", Set("sa"), Set()),
      PrivacyDeclaration(0L, 0L, "d", Set("cb2"), "ua", "qa", Set("sa1"), Set())
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a,b,c,d", Set("ca", "cb"), "ua", "qa", Set("sa"), Set()))

  }

  test("test diff declarations") {

    def diff(aDecs: Seq[PrivacyDeclaration], bDecs: Seq[PrivacyDeclaration]): Set[PrivacyDeclaration] =
      systemEvaluator.diffDeclarations(3L, aDecs, bDecs)

    //diff of identical
    diff(
      Seq(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "b", Set("ca"), "ua", "qa", Set("sa"), Set()))
    ) shouldBe Set()
    //diff of child/parent cat
    diff(
      Seq(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "b", Set("ca1"), "ua", "qa", Set("sa"), Set()))
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set(), Set()))
    //diff of child/parent subject-cat
    diff(
      Seq(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "b", Set("ca"), "ua", "qa", Set("sa1"), Set()))
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a", Set(), "ua", "qa", Set("sa"), Set()))
    //diff of child/parent both
    diff(
      Seq(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "b", Set("ca1"), "ua", "qa", Set("sa1"), Set()))
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set()))
    //diff of child/parent both split between multiple
    diff(
      Seq(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set())),
      Seq(PrivacyDeclaration(0L, 0L, "b", Set("ca1"), "ua", "qa", Set("sa1"), Set()))
    ) shouldBe Set(PrivacyDeclaration(0L, 0L, "a", Set("ca"), "ua", "qa", Set("sa"), Set()))
    //split by use
    diff(
      Seq(
        PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set("sa1"), Set()),
        PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua1", "qa", Set("sa1"), Set())
      ),
      Seq(
        PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua", "qa", Set("sa1"), Set()),
        PrivacyDeclaration(0L, 0L, "b", Set("ca2"), "ua1", "qa", Set("sa1"), Set())
      )
    ) shouldBe Set(
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua", "qa", Set(), Set()),
      PrivacyDeclaration(0L, 0L, "a", Set("ca1"), "ua1", "qa", Set(), Set())
    )

  }

}
