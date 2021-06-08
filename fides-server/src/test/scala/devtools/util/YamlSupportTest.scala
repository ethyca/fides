package devtools.util

import devtools.Generators.RegistryGen
import devtools.domain.Registry
import devtools.util.ProtocolTestClasses._
import devtools.util.YamlSupport.{toAST, yamlObjectToMergeable}
import net.jcazevedo.moultingyaml.{DefaultYamlProtocol, _}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

import scala.util.{Failure, Success}
/** Some test classes */
import devtools.util.FidesYamlProtocols._
class YamlSupportTest extends AnyFunSuite with Matchers {

  object MyYamlProtocols extends DefaultYamlProtocol {
    implicit val ThingFormat: YamlFormat[Thing]               = yamlFormat3(Thing)
    implicit val ThingHolderFormat: YamlFormat[ThingHolder]   = yamlFormat2(ThingHolder)
    implicit val SimpleFormat: YamlFormat[Simple]             = yamlFormat2(Simple)
    implicit val EitherHolderFormat: YamlFormat[EitherHolder] = yamlFormat2(EitherHolder)
  }

  import MyYamlProtocols._
  def lines(s: String): YamlValue = s.split(",").mkString("\n").parseYaml

  test("read simple yaml") {
    lines("color: red,priority: 2").convertTo[Thing] shouldEqual Thing("red", 2, None)
    lines("color: red,priority: 2,count: 3").convertTo[Thing] shouldEqual Thing("red", 2, Some(3))
  }

  test(testName = "read simple yaml list") {
    lines("- color: red,  priority: 2,- color: blue,  priority: 1")
      .convertTo[List[Thing]] shouldEqual List(Thing("red", 2, None), Thing("blue", 1, None))
  }

  test(testName = "read nested yaml objects") {
    val yaml: String =
      """name: Foo
        |things:
        |- color: red
        |  priority: 2
        |  count: 1
        |- color: blue
        |  priority: 1
        |""".stripMargin

    yaml.parseYaml
      .convertTo[ThingHolder] shouldEqual ThingHolder("Foo", List(Thing("red", 2, Some(1)), Thing("blue", 1, None)))

    YamlSupport.parseToObj[Map[String, Any]](yaml) shouldBe
      Success(
        Map(
          "things" -> Vector(
            Map("color" -> "red", "priority"  -> 2, "count" -> 1),
            Map("color" -> "blue", "priority" -> 1)
          ),
          "name" -> "Foo"
        )
      )
  }

  test(testName = "DeserializationException thrown on parse to object with incorrect yaml") {
    an[DeserializationException] should be thrownBy lines("color: red").convertTo[Thing]
  }

  test(testName = "parseAsObject returns Failure on un-parsable String") {
    val badString = "- A\n\nb"
    YamlSupport.parseToObj[Map[String, Any]](badString) should be(a[Failure[_]])
  }

  def yToM(y: YamlObject): Map[String, Any] = YamlSupport.fromAST(y)(FidesYamlProtocols.MapAnyFormat).get
  def mToY(m: Map[String, Any]): YamlObject = YamlSupport.toAST(m)(FidesYamlProtocols.MapAnyFormat).asYamlObject()

  test("test yaml object mergeAfter") {
    //   val a = toAST(Map("a" -> "1", "b" -> 2)).asYamlObject()
    val a = Map("a" -> "1", "b" -> 2)
    val b = Map("a" -> "replaced", "x" -> "foo")
    yToM(mToY(a).mergeBefore(b)) shouldEqual Map("a" -> "replaced", "b" -> 2, "x" -> "foo")
    yToM(mToY(a).mergeAfter(b)) shouldEqual Map("a" -> "1", "b" -> 2, "x" -> "foo")

  }

  test("parseEither") {
    //left side
    val e1  = EitherHolder("A", Some(Left(Seq(1, 2))))
    val e11 = YamlSupport.fromAST[EitherHolder](toAST(e1))
    e11.get shouldEqual e1

    //right side
    val e2  = EitherHolder("A", Some(Right(Seq(Simple(1, "A"), Simple(2, "B")))))
    val e21 = YamlSupport.fromAST[EitherHolder](toAST(e2))
    e21.get shouldEqual e2

  }

  test("test custom registry serializer") {
    val r      = RegistryGen.sample.get.copy(systems = Some(Left(Seq(1, 2, 3))))
    val j      = YamlSupport.toAST[Registry](r)
    val s      = YamlSupport.dumps(j)
    val jFromS = YamlSupport.loads(s).get
    jFromS shouldEqual j
    val rFromJ = YamlSupport.fromAST[Registry](jFromS).get
    rFromJ shouldEqual r

  }

}
