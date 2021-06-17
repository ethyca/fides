package devtools.rating

import devtools.TestUtils
import org.scalatest.funsuite.AnyFunSuite

class RegistryEvaluatorTest extends AnyFunSuite with TestUtils {

  test("test cycle check") {
    //  test("test cycle check") {
    //    val s1 = systemOf("a").copy(systemDependencies = Set("a"))
    //    messages(e => approvalChecks.cycleCheck(Seq(s1), e)).errors.toSeq should containMatchString("cyclic reference")
    //  }

  }

  test("test multiple system approval") {}

//  private val approvalChecks = App.registryApprovalChecks
//
//  def messages(f: MessageCollector => Unit): MessageCollector = {
//    val m = new MessageCollector()
//    f(m)
//    m
//  }
//

//
//  test("test validate dataset dependencies") {
//    val s1      = systemOf("a").copy(datasets = Set("ax", "bx", "cx"))
//    val dataset = datasetOf("ax")
//    messages(e =>
//      approvalChecks.validateDatasetsExist(Seq(s1), Seq(dataset), e)
//    ).errors.toSeq should containMatchString(
//      "These datasets were declared as dependencies but were not found"
//    )
//  }
//  test("test dataset field declarations") {
//
//    val fullyPopulatedField = datasetFieldOf("all")
//      .copy(dataCategories = Some(availableDataCategories.toSet), dataQualifier = Some("identified_data"))
//    val dataset1 = datasetOf("d1", datasetTableOf("d1t1", fullyPopulatedField))
//    val s2 =
//      systemOf("b").copy(declarations =
  //      )
//    messages(e =>
//      approvalChecks.validateDatasetsExist(Seq(s2), Seq(dataset1), e)
//    ).warnings.toSeq should containMatchString(
//      "These categories exist for qualifer"
//    )
//  }
//
//
//  test("test system declaration dependencies") {
//
//    def testDependencies(parent: Seq[Declaration], child: Seq[Declaration]): MessageCollector = {
//      val s1 = systemOf("a").copy(systemDependencies = Set("b"), declarations = parent)
//      val s2 = systemOf("b").copy(declarations = child)
//      messages(e => approvalChecks.checkDeclarationsOfDependentSystems(s1, Seq(s1, s2), e))
//    }
//
//    //categories
//    def cat_root1       = "customer_content_data"
//    def cat_root1_child = "credentials"
//    def cat_root2       = "derived_data"
//
//    //subject categories
//    def scat_root1 = "customer"
//    def scat_root2 = "patient"
//
//    //qualifiers
//    def q_root = "aggregated_data"
//    //def q_child = "anonymized_data"
//
//    //use
//    def use_root1 = "share"
//    //def use_root1_child = "share_when_required_to_provide_the_service"
//    def use_root2 = "personalize"
//
//    //Just different category
//    testDependencies(
//      Seq(Declaration("test2", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
//      Seq(Declaration("test3", Set(cat_root2), use_root1, q_root, Set(scat_root1)))
//    ).warnings.toSeq should containMatchString("The system b includes privacy declarations that do not exist in a")
//
//    //Just different subject category
//    testDependencies(
//      Seq(Declaration("test4", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
//      Seq(Declaration("test5", Set(cat_root1), use_root1, q_root, Set(scat_root2)))
//    ).warnings.toSeq should containMatchString("The system b includes privacy declarations that do not exist in a")
//
//    //child with child cat, same qualifier/use is ok
//
//    testDependencies(
//      Seq(Declaration("test6", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
//      Seq(Declaration("test7", Set(cat_root1_child), use_root1, q_root, Set(scat_root1)))
//    ).warnings.size shouldEqual 0
//
//    //child with parent cat, same qualifier/use -> message
//
//    testDependencies(
//      Seq(Declaration("test8", Set(cat_root1_child), use_root1, q_root, Set(scat_root1))),
//      Seq(Declaration("test9", Set(cat_root1), use_root1, q_root, Set(scat_root1)))
//    ).warnings.toSeq should containMatchString("The system b includes privacy declarations that do not exist in a")
//
//    //child with NEW (qualifier/use) pair
//    testDependencies(
//      Seq(Declaration("test10", Set(cat_root1), use_root1, q_root, Set(scat_root1))),
//      Seq(
//        Declaration("test11", Set(cat_root1_child), use_root1, q_root, Set(scat_root1)),
//        Declaration("test12", Set(cat_root2), use_root2, q_root, Set(scat_root1))
//      )
//    ).warnings.toSeq should containMatchString("The system b includes privacy declarations that do not exist in a")
//
//  }
}
