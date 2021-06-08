package devtools.controller

import devtools.App
import devtools.Generators.SystemObjectGen
import devtools.domain.SystemObject
import devtools.util.JsonSupport.{dumps => jdumps, parseToObj => jParseToObj, toAST => jToAST}
import devtools.util.YamlSupport.{dumps => ydumps, toAST => yToAST}
import scala.util.{Success, Try}

class SystemControllerTest
  extends ControllerTestBase[SystemObject, Long]("system", SystemObjectGen, App.systemController) {
  override def editValue(t: SystemObject): SystemObject = generator.sample.get.copy(id = t.id)

  override def isValid(t: SystemObject): Boolean = t.id > 0 && t.fidesKey.nonEmpty

  override def withoutMergeValues(t: SystemObject): Map[String, Any] =
    super.withoutMergeValues(t.copy(lastUpdateTime = None, creationTime = None, versionStamp = None))

  test("test find by unique key") {
    var testInstance: SystemObject = generator.sample.get

    post(s"/$path", jdumps(withoutMergeValues(testInstance)), withTestHeaders("Content-Type" -> "application/json")) {
      shouldBe200(status, body)
      val returned: Try[SystemObject] = parseBody[SystemObject](body)
      returned should be(a[Success[_]])
      //returned instance is == excluding id
      compareWithoutMergeValues(returned.get, testInstance)
      testInstance = returned.get
      ids.add(testInstance.id)
    }

    get(s"/$path/find/${testInstance.fidesKey}", headers = testHeaders) {
      shouldBe200(status, body)
      val returned: Try[SystemObject] = parseBody[SystemObject](body)
      compareWithoutMergeValues(returned.get, testInstance)

    }

  }
}
