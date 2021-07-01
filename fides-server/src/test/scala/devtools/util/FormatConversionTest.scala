package devtools.util

import devtools.Generators._
import devtools.util.{JsonSupport => J, YamlSupport => Y}
import net.jcazevedo.moultingyaml.{YamlFormat, YamlValue}
import org.json4s.{Formats, JValue}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

import scala.util.Success
class FormatConversionTest extends AnyFunSuite with Matchers {

  implicit val formats: Formats = JsonSupport.formats
  import FidesYamlProtocols._

  def testYaml[T <: AnyRef](t: T)(implicit format: YamlFormat[T], manifest: Manifest[T]): Unit = {

    val ast: YamlValue = Y.toAST[T](t)
    val s: String      = Y.dumps(ast)
    Y.parseToObj[T](s) shouldEqual Success(t)
    Y.loads(s) shouldEqual (Success(ast))
    Y.fromAST[T](ast) shouldEqual (Success(t))
  }

  def testJson[T <: AnyRef](t: T)(implicit manifest: Manifest[T]): Unit = {
    val ast: JValue = J.toAST[T](t)
    val s: String   = J.dumps(ast)
    J.parseToObj[T](s) shouldEqual Success(t)
    J.loads(s) shouldEqual (Success(ast))
    J.fromAST[T](ast) shouldEqual (Success(t))
  }

  def testObject[T <: AnyRef](t: T)(implicit format: YamlFormat[T], manifest: Manifest[T]): Unit = {
    testYaml[T](t)
    testJson[T](t)
  }

  test("test approval format conversion") {
    testObject(ApprovalGen.sample.get)
  }

  test("test data category format conversion") {
    testObject(DataCategoryGen.sample.get)
  }

  test("test data qualifier format conversion") {
    testObject(DataQualifierGen.sample.get)
  }

  test("test data use format conversion") {
    testObject(DataUseGen.sample.get)
  }

  test("test data subject category format conversion") {
    testObject(DataSubjectGen.sample.get)
  }

  test("test declaration format conversion") {
    testObject(DeclarationGen.sample.get)
  }

  test("test org format conversion") {
    testObject(OrgGen.sample.get)
  }
  test("test policy format conversion") {
    testObject(PolicyGen.sample.get)
  }

  test("testpolicy rule format conversion") {
    testObject(PolicyRuleGen.sample.get)
  }

  test("test system format conversion") {
    testObject(SystemObjectGen.sample.get)
  }

  test("test user format conversion") {
    testObject(UserGen.sample.get)
  }
  test("test dataset format conversion") {
    testObject(DatasetGen.sample.get)
  }

  test("test dataset field format conversion") {
    testObject(DatasetFieldGen.sample.get)
  }

}
