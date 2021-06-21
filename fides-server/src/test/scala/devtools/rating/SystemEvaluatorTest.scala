package devtools.rating

import devtools.Generators.SystemObjectGen
import devtools.domain.enums.ApprovalStatus
import devtools.domain.policy.Declaration
import devtools.{App, TestUtils}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.concurrent.ExecutionContext
class SystemEvaluatorTest extends AnyFunSuite with TestUtils {

  implicit val context: ExecutionContext = App.executionContext
  private val systemEvaluator            = new SystemEvaluator(App.daos)

  test("test rate rating catch missing dataset") {
    val sys = SystemObjectGen.sample.get
      .copy(fidesKey = "a", declarations = Seq(), systemDependencies = Set(), datasets = Set("missing1", "missing2"))
    val v: SystemEvaluation = systemEvaluator.evaluateSystem(sys, Seq(), Seq(), Seq())

    v.errors should containMatchString(
      "The referenced datasets \\[.*\\] were not found"
    )
    v.overallApproval shouldEqual ApprovalStatus.ERROR
  }
  test("test rate rating catch missing system dependency") {
    val sys = SystemObjectGen.sample.get
      .copy(fidesKey = "a", declarations = Seq(), systemDependencies = Set("missing1", "missing2"), datasets = Set())
    val v: SystemEvaluation = systemEvaluator.evaluateSystem(sys, Seq(), Seq(), Seq())

    v.errors should containMatchString(
      "The referenced systems \\[.*\\] were not found."
    )

    v.overallApproval shouldEqual ApprovalStatus.ERROR
  }

  test("test self reference") {
    val sys                 = SystemObjectGen.sample.get.copy(fidesKey = "a", declarations = Seq(), systemDependencies = Set("a"))
    val v: SystemEvaluation = systemEvaluator.evaluateSystem(sys, Seq(), Seq(), Seq())

    v.errors should containMatchString(
      "Invalid self reference"
    )
    v.overallApproval shouldEqual ApprovalStatus.ERROR
  }

  //categories
  private def cat_root1        = "customer_content_data"
  private def cat_root1_child1 = "credentials"
  private def cat_root2        = "derived_data"
  private def allChildrenOfCatRoot1 =
    Set(
      "credentials",
      "customer_contact_lists",
      "personal_health_data_and_medical_records",
      "personal_genetic_data",
      "personal_biometric_data",
      "personal_data_of_children",
      "political_opinions",
      "financial_details",
      "sensor_measurement_data"
    )

  //subject categories
  private def scat_root1 = "customer"
  private def scat_root2 = "patient"

  //qualifiers
  private def q_root  = "aggregated_data"
  private def q_child = "anonymized_data"

  //use
  private def use_root1 = "share"
  private def use_root2 = "personalize"
  test("test system declaration dependencies") {

    def testDependencies(parent: Seq[Declaration], child: Seq[Declaration]): Seq[String] = {
      val s1 = systemOf("a").copy(systemDependencies = Set("b"), declarations = parent)
      val s2 = systemOf("b").copy(declarations = child)
      systemEvaluator.checkDeclarationsOfDependentSystems(s1, Seq(s2))
    }

    //Just different category
    testDependencies(
      Seq(Declaration("test2", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq(Declaration("test3", Set(cat_root2), use_root1, q_root, Set(scat_root1)))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //Just different subject category
    testDependencies(
      Seq(Declaration("test4", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq(Declaration("test5", Set(cat_root1), use_root1, q_root, Set(scat_root2)))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //child with child cat, same qualifier/use is ok

    testDependencies(
      Seq(Declaration("test6", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq(Declaration("test7", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1)))
    ).size shouldEqual 0

    //child with parent cat, same qualifier/use -> message

    testDependencies(
      Seq(Declaration("test8", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1))),
      Seq(Declaration("test9", Set(cat_root1), use_root1, q_root, Set(scat_root1)))
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

    //child with NEW (qualifier/use) pair
    testDependencies(
      Seq(Declaration("test10", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq(
        Declaration("test11", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1)),
        Declaration("test12", Set(cat_root2), use_root2, q_root, Set(scat_root1))
      )
    ) should containMatchString("The system b includes privacy declarations that do not exist in a")

  }

  test("check dependent dataset privacy gamut") {

    type DatasetSpec = (String, Set[String]) //(qualifier, categories)

    def testDependencies(declarations: Seq[Declaration], datasetSpecs: Seq[DatasetSpec]): Seq[String] = {
      val s1 = systemOf("a").copy(declarations = declarations)
      val dataset = datasetOf(
        "b",
        datasetTableOf(
          "c",
          datasetSpecs.zipWithIndex.map(t =>
            datasetFieldOf(s"f${t._2}").copy(dataCategories = Some(t._1._2), dataQualifier = Some(t._1._1))
          ): _*
        )
      )
      systemEvaluator.checkDependentDatasetPrivacyDeclaration(s1, Seq(dataset))
    }

    //System is child value category. Diff should be the parent that only exists in the dataset spec
    testDependencies(
      Seq(Declaration("test2", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq((q_root, Set(cat_root1_child1)))
    ) should containMatchString(
      "These categories exist for qualifier aggregated_data in this dataset but do not appear with that qualifier in the dependant system"
    )

    //unrelated category
    testDependencies(
      Seq(Declaration("test2", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq((q_root, Set(cat_root2)))
    ) should containMatchString(
      "These categories exist for qualifier aggregated_data in this dataset but do not appear with that qualifier in the dependant system"
    )

    //TODO these are failing and need to be rewritten:
    //dataset qualifier and/or categories represent a wider gamut than the system declaration
    /*
    testDependencies(
      Seq(Declaration("test2", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
      Seq(( q_child, Set(cat_root1)))
    )  should containMatchString("The system b includes privacy declarations that do not exist in a")

    //dataset contains more open qualifier and category
    testDependencies(
      Seq(Declaration("test2", Set(cat_root1_child1), use_root1, q_root, Set(scat_root1))),
      Seq((q_child , Set(cat_root1)))
    )  should containMatchString("The system b includes privacy declarations that do not exist in a")
     */

  }

  test("test merge declarations") {
    def merge(declarations:Declaration*) =  systemEvaluator.mergeDeclarations(3L, declarations)


    //merge identical elements should return same element
    merge(Declaration("a", Set("ca","ca1"), "ua", "qa", Set("sa","sa1")),
      Declaration("a", Set("ca","ca1"), "ua", "qa", Set("sa","sa1")),
      Declaration("a", Set("ca","ca1"), "ua", "qa", Set("sa","sa1"))) shouldBe Set(Declaration("a", Set("ca"), "ua", "qa", Set("sa")))
    //same split into 2 declarations
    merge(Declaration("a", Set("ca"), "ua", "qa", Set("sa")),
      Declaration("b", Set("ca1"), "ua", "qa", Set("sa1")))  shouldBe Set(Declaration("a,b", Set("ca"), "ua", "qa", Set("sa")))

    //merge elements in a single declaration
    merge(Declaration("a", Set("ca","ca1"), "ua", "qa", Set("sa","sa1"))) shouldBe Set(Declaration("a", Set("ca"), "ua", "qa", Set("sa")))
   //same split into 2 declarations
    merge(Declaration("a", Set("ca"), "ua", "qa", Set("sa")),
      Declaration("b", Set("ca1"), "ua", "qa", Set("sa1")))  shouldBe Set(Declaration("a,b", Set("ca"), "ua", "qa", Set("sa")))

    merge(Declaration("a", Set("ca1"), "ua", "qa", Set("sa")),
      Declaration("b", Set("ca2"), "ua", "qa", Set("sa1")))  shouldBe Set(Declaration("a,b", Set("ca"), "ua", "qa", Set("sa")))

    merge(Declaration("a", Set("ca1"), "ua", "qa", Set("sa")),
      Declaration("b", Set("ca2"), "ua", "qa", Set("sa1")))  shouldBe Set(Declaration("a,b", Set("ca"), "ua", "qa", Set("sa")))

    //different use values
    merge(Declaration("a", Set("ca1"), "ua", "qa", Set("sa")), Declaration("b", Set("ca2"), "ua", "qa", Set("sa1")),
      Declaration("c", Set("ca1"), "ub", "qa", Set("sa")), Declaration("d", Set("ca2"), "ub", "qa", Set("sa1"))
    )  shouldBe Set(Declaration("a,b", Set("ca"), "ua", "qa", Set("sa")), Declaration("c,d", Set("ca"), "ub", "qa", Set("sa")))

    //same use values, different category roots
    merge(Declaration("a", Set("ca1"), "ua", "qa", Set("sa")), Declaration("b", Set("ca2"), "ua", "qa", Set("sa1")),
      Declaration("c", Set("cb1"), "ua", "qa", Set("sa")), Declaration("d", Set("cb2"), "ua", "qa", Set("sa1"))
    )  shouldBe Set(Declaration("a,b,c,d", Set("ca","cb"), "ua", "qa", Set("sa")))



  }

  test("test diff declarations") {

    def diff(aDecs:Seq[Declaration],bDecs:Seq[Declaration]): Set[Declaration] =  systemEvaluator.diffDeclarations(3L, aDecs, bDecs)

    //diff of identitcal
    diff(Seq(Declaration( "a",Set("ca"), "ua", "qa", Set("sa"))), Seq( Declaration("b",Set("ca"), "ua", "qa", Set("sa")))) shouldBe Set()
    //diff of child/parent cat
    diff(Seq(Declaration( "a",Set("ca"), "ua", "qa", Set("sa"))), Seq( Declaration("b",Set("ca1"), "ua", "qa", Set("sa")))) shouldBe Set(Declaration("a",Set("ca"), "ua", "qa", Set()))
    //diff of child/parent subject-cat
    diff(Seq(Declaration( "a",Set("ca"), "ua", "qa", Set("sa"))), Seq( Declaration("b",Set("ca"), "ua", "qa", Set("sa1")))) shouldBe Set(Declaration("a",Set(), "ua", "qa", Set("sa")))
    //diff of child/parent both
    diff(Seq(Declaration( "a",Set("ca"), "ua", "qa", Set("sa"))), Seq( Declaration("b",Set("ca1"), "ua", "qa", Set("sa1")))) shouldBe Set(Declaration("a",Set("ca"), "ua", "qa", Set("sa")))
    //diff of child/parent both split between multiple
    diff(Seq(Declaration( "a",Set("ca"), "ua", "qa", Set("sa"))), Seq( Declaration("b",Set("ca1"), "ua", "qa", Set("sa1")))) shouldBe Set(Declaration("a",Set("ca"), "ua", "qa", Set("sa")))
    //split by use
    diff(Seq(Declaration( "a",Set("ca1"), "ua", "qa", Set("sa1")), Declaration( "a",Set("ca1"), "ua1", "qa", Set("sa1")) ),
      Seq( Declaration("b",Set("ca2"), "ua", "qa", Set("sa1")),  Declaration("b",Set("ca2"), "ua1", "qa", Set("sa1")))) shouldBe Set(Declaration("a",Set("ca1"), "ua", "qa", Set()),Declaration("a",Set("ca1"), "ua1", "qa", Set()))


    //split by qualifier


    //diff child/parent


    //diff child1/child2

    //diff a,b/b == a

    //diff (a,b,c) ... (b,c,d) == (a,d)?

  }
}
