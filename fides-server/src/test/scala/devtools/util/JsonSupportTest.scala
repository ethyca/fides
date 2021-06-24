package devtools.util

import devtools.TestUtils
import devtools.domain.Dataset
import devtools.domain.enums.ApprovalStatus.FAIL
import devtools.domain.enums.AuditAction.CREATE
import devtools.domain.enums.PolicyAction.ACCEPT
import devtools.domain.enums.Role.ADMIN
import devtools.domain.enums.RuleInclusion.ANY
import devtools.domain.policy.Policy
import devtools.util.JsonSupport._
import devtools.util.ProtocolTestClasses._
import org.json4s.JsonDSL._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.{a, be}
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.util.{Failure, Success}

class JsonSupportTest extends AnyFunSuite with TestUtils {

  test(testName = "parse to ast") {
    loads("""{"A":1,"B":[1,2,3]}""") shouldEqual Success(("A" -> 1) ~ ("B" -> Seq(1, 2, 3)))
  }

  test(testName = "errors") {
    parseToObj("""{"fidesKey":"this is bad json""") should be(a[Failure[_]])
  }
  case class H(name: String, vals: Set[String])

  test(testName = "serialize case classes") {

    val v = ThingHolder("Foo", List(Thing("red", 2, Some(1)), Thing("blue", 1, None)))

    parseToObj[ThingHolder](dumps(v)) shouldEqual Success(v)

    parseToObj[Map[String, Any]](dumps(v)) shouldEqual Success(
      Map(
        "name" -> "Foo",
        "things" -> List(
          Map("color" -> "red", "priority"  -> 2, "count" -> 1),
          Map("color" -> "blue", "priority" -> 1)
        )
      )
    )
  }

  test("parse object to json AST") {
    toAST(Simple(1, "A")) shouldEqual ("i" -> 1) ~ ("name" -> "A")
  }

  test("parseEither") {
    //left side
    val e1  = EitherHolder("A", Some(Left(Seq(1, 2))))
    val e11 = JsonSupport.fromAST[EitherHolder](toAST(e1))
    e11.get shouldEqual e1

    //right side
    val e2  = EitherHolder("A", Some(Right(Seq(Simple(1, "A"), Simple(2, "B")))))
    val e21 = JsonSupport.fromAST[EitherHolder](toAST(e2))
    e21.get shouldEqual e2

  }

  test("test Enums") {
    val e = EnumHolder(FAIL, CREATE, ACCEPT, ANY, ADMIN)
    JsonSupport.parseToObj[EnumHolder](JsonSupport.dumps(e)) shouldEqual Success(e)
  }

  test("test difference"){
    val a = JsonSupport.toAST(Map("A"->1, "B"->2, "C"->3, "E"->5))
    val b = JsonSupport.toAST(Map( "B"->2, "C"->3,"D"-> 4, "E"->6))
    val a_to_b = JsonSupport.fromAST[Map[String,Any]](JsonSupport.difference(a,b)).get
    val b_to_a = JsonSupport.fromAST[Map[String,Any]](JsonSupport.difference(b,a)).get
    a_to_b shouldEqual Map("changed" -> Map("E" -> 6), "added" -> Map("D" -> 4), "deleted" -> Map("A" -> 1))
    b_to_a shouldEqual Map("changed" -> Map("E" -> 5), "added" -> Map("A" -> 1), "deleted" -> Map("D" -> 4))
  }

  test("test parse nested datasets") {
    val raw =
      """
    {
      "id":1,
      "organizationId": 1,
      "fidesKey": "test-dataset",
      "versionStamp": 0,
      "name": "my test dataset",
      "location": "us-east-1",
      "datasetType": "SQL",
      "tables": [
         {
        "name": "table1",
        "fields": [ {
          "name": "field1",
          "dataCategories": [
          "credentials"
          ],
          "dataQualifier": "aggregated_data"
        },
        {
          "name": "field2",
          "dataCategories": [],
          "dataQualifier": "pseudonymized_data"
        }
        ]
      },
      {
        "name": "table2"
      }
      ]
    }
  }"""

    val r      = JsonSupport.parseToObj[Dataset](raw)
    val tables = r.get.tables.get
    tables.size shouldEqual 2
    val table1 = tables.find(_.name == "table1").get
    table1.fields.get.map(_.name).toSet shouldEqual Set("field1", "field2")
  }

  test("test parse nested policy rules") {
    val raw = """{
                |  "id": 1,
                |  "organizationId": 1,
                |  "fidesKey": "test policy 1",
                |  "versionStamp": 0,
                |  "description": "random policy",
                |  "rules": [
                |    {
                |      "organizationId": 1,
                |      "fidesKey": "AAAAAAAA",
                |      "description": "random rule 1",
                |      "dataCategories": {
                |        "inclusion": "ANY",
                |        "values": []
                |      },
                |      "dataUses": {
                |        "inclusion": "NONE",
                |        "values": [
                |          "provide"
                |        ]
                |      },
                |      "dataSubjectCategories": {
                |        "inclusion": "ANY",
                |        "values": []
                |      },
                |      "dataQualifier": "unlinked_pseudonymized_data",
                |      "action": "REQUIRE"
                |    },
                |    {
                |      "organizationId": 1,
                |      "fidesKey": "BBBBBBBB",
                |      "description": "random rule 2",
                |      "dataCategories": {
                |        "inclusion": "ANY",
                |        "values": []
                |      },
                |      "dataUses": {
                |        "inclusion": "ANY",
                |        "values": [
                |          "provide"
                |        ]
                |      },
                |      "dataSubjectCategories": {
                |        "inclusion": "ANY",
                |        "values": []
                |      },
                |      "dataQualifier": "identified_data",
                |      "action": "REJECT"
                |    }
                |  ]
                |}""".stripMargin

    val r     = JsonSupport.parseToObj[Policy](raw)
    val rules = r.get.rules.get
    rules.size shouldEqual 2
    rules.map(_.fidesKey).toSet shouldEqual Set("AAAAAAAA", "BBBBBBBB")

  }

}
