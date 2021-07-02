package devtools.controller

import devtools.App
import devtools.Generators.SystemObjectGen
import devtools.domain.{Approval, SystemObject}
import devtools.util.JsonSupport.{dumps => jdumps}

import scala.util.{Success, Try}

class SystemControllerTest
  extends ControllerTestBase[SystemObject, Long]("system", SystemObjectGen, App.systemController) {
  override def editValue(t: SystemObject): SystemObject = generator.sample.get.copy(id = t.id)

  override def isValid(t: SystemObject): Boolean = t.id > 0 && t.fidesKey.nonEmpty

  override def withoutMergeValues(t: SystemObject): Map[String, Any] =
    super.withoutMergeValues(t.copy(lastUpdateTime = None, creationTime = None, versionStamp = None))

  var testInstance: SystemObject = generator.sample.get

  test("test find by unique key") {

    post(s"/$path", jdumps(withoutMergeValues(testInstance)), withTestHeaders("Content-Type" -> "application/json")) {
      shouldBe200(status, body)
      val returned: Try[SystemObject] = parseBody[SystemObject](body)
      returned should be(a[Success[_]])
      // returned instance is == excluding id
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

  test("test approval endpoints") {
    def approval(body: String): Approval = parseBody[Approval](body).get

    var apr: Approval = null

    get(s"/$path/evaluate/${testInstance.fidesKey}", headers = testHeaders) {
      apr = approval(body)
      apr.action shouldEqual "evaluate"
    }

    /* retrieving "last" returns the same approval we just created */
    get(s"/$path/evaluate/${testInstance.fidesKey}/last", headers = testHeaders) {
      approval(body).id shouldEqual apr.id
    }
    /* create a new approval. Id should be greater.*/
    get(s"/$path/evaluate/${testInstance.fidesKey}", headers = testHeaders) {
      val v = approval(body)
      v.id should be > apr.id
      apr = v
      apr.action shouldEqual "evaluate"

    }

    /* last should now refer to most recent.*/
    get(s"/$path/evaluate/${testInstance.fidesKey}/last", headers = testHeaders) {
      approval(body).id shouldEqual apr.id
    }

    post(
      s"/$path/evaluate/dry-run",
      jdumps(testInstance),
      headers = withTestHeaders("Content-Type" -> "application/json")
    ) {
      approval(body).action shouldEqual "dry-run"
    }
  }

}
