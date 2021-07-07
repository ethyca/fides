package devtools.domain

import devtools.Generators.UserGen
import devtools.TestUtils
import devtools.controller.RequestContext
import devtools.domain.definition.IdType
import devtools.persist.service.definition.Service
import devtools.util.{JsonSupport, YamlSupport, waitFor}
import net.jcazevedo.moultingyaml.{YamlFormat, YamlValue}
import org.json4s.{Formats, JValue}
import org.scalacheck.Gen
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.{a, convertToAnyShouldWrapper}

import scala.collection.mutable.{HashSet => MHashSet}
import scala.util.{Failure, Success, Try}

abstract class DomainObjectTestBase[T <: IdType[T, PK], PK](
  val service: Service[T, PK, _],
  val generator: Gen[T],
  val yamlFormat: YamlFormat[T]
)(implicit manifest: Manifest[T])
  extends AnyFunSuite with TestUtils with BeforeAndAfterAll {
  val requestContext: RequestContext = RequestContext(UserGen.sample.get.copy(id = 1, organizationId = 1))
  val ids: MHashSet[PK]              = new MHashSet[PK]
  implicit val jsonFormats: Formats  = JsonSupport.formats
  /** Cleanup any created records */
  override def afterAll(): Unit = {
    ids.foreach(id => service.delete(id, requestContext))
  }

  val typeName: String = manifest.runtimeClass.getSimpleName

  def editValue(t: T): T

  /** Override this to maskForComparison fields that should not be part of equality comparisons */
  def maskForComparison(t: T): T = t

  /** Basic CRUD operations tests */
  test(testName = s"$typeName: test CRUD ") {

    val initial           = generator.sample.get
    val createResponse: T = waitFor(service.create(initial, requestContext))
    val inserted          = createResponse
    ids.add(inserted.id)
    try {
      val getByIdResponse = waitFor(service.findById(inserted.id, requestContext))
      getByIdResponse should be(a[Some[_]])
      val queried = getByIdResponse.get
      maskForComparison(queried) shouldBe maskForComparison(inserted)

      val edited = editValue(queried)
      //val updateResponse = waitFor(service.update(edited,requestContext))
      val updated = waitFor(service.findById(inserted.id, requestContext)).get
      updated.id shouldBe inserted.id

    } finally {
      val deleteResponse = waitFor(service.delete(inserted.id, requestContext))
      deleteResponse.shouldEqual(1)
    }
  }

  /** Generate a Try via a function that takes a legit value and generates a new value that
    * will violate a constraint on insert
    */
  def testInsertConstraint(f: T => T): Unit = {
    val initial           = generator.sample.get
    val createResponse: T = waitFor(service.create(initial, requestContext))
    val inserted          = createResponse
    try {
      val failValue = f(inserted)
      Try(waitFor(service.create(failValue, requestContext))) should be(a[Failure[_]])
    } finally {
      val deleteResponse = waitFor(service.delete(inserted.id, requestContext))
      deleteResponse shouldEqual 1
    }
  }

  test(s"$typeName test YAML conversion") {
    val initial: T         = generator.sample.get
    val yamlAST: YamlValue = YamlSupport.toAST(initial)(yamlFormat)
    /* conversion back to initial value works:*/
    val unconverted: Try[T] = YamlSupport.fromAST[T](yamlAST)(yamlFormat)
    unconverted should be(a[Success[_]])
    unconverted.get shouldEqual initial
    /* yaml str */
    val s: String      = YamlSupport.dumps(yamlAST)
    val unconvertedAST = YamlSupport.loads(s)
    unconvertedAST should be(a[Success[_]])
    unconvertedAST.get shouldEqual yamlAST
    /* to/from json.*/
    val json: JValue        = YamlSupport.toJson(yamlAST)
    val unconvertedFromJson = JsonSupport.toYaml(json)
    unconvertedFromJson shouldEqual yamlAST
  }

  test(s"$typeName test JSON conversion") {
    val initial: T      = generator.sample.get
    val jsonAST: JValue = JsonSupport.toAST(initial)
    /* conversion back to initial value works:*/
    val unconverted: Try[T] = JsonSupport.fromAST[T](jsonAST)
    unconverted should be(a[Success[_]])
    maskForComparison(unconverted.get) shouldEqual maskForComparison(initial)
    /* yaml str */
    val s: String                   = JsonSupport.dumps(jsonAST)
    val unconvertedAST: Try[JValue] = JsonSupport.loads(s)
    unconvertedAST should be(a[Success[_]])
    unconvertedAST.get shouldEqual jsonAST
    /* to/from json.*/
    val yaml: YamlValue     = JsonSupport.toYaml(jsonAST)
    val unconvertedFromYaml = YamlSupport.toJson(yaml)
    /* raw json may be re-ordered, but hydrating back to the initial object
    should always give us the same object
     */
    JsonSupport.fromAST[T](unconvertedFromYaml).get shouldEqual initial

  }

}
