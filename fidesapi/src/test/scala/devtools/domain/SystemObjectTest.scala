package devtools.domain
import devtools.App
import devtools.Generators.SystemObjectGen
import devtools.exceptions.InvalidDataException
import devtools.util.{FidesYamlProtocols, waitFor}
import faker._
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper
import slick.jdbc.PostgresProfile.api._

class SystemObjectTest
  extends DomainObjectTestBase[SystemObject, Long](
    App.systemService,
    SystemObjectGen,
    FidesYamlProtocols.SystemObjectFormat
  ) {
  private val db                                        = App.database
  override def editValue(t: SystemObject): SystemObject = t.copy(fidesKey = Name.name)
  override def maskForComparison(t: SystemObject): SystemObject =
    t.copy(creationTime = None, lastUpdateTime = None, privacyDeclarations = None)

  /** How many times is this category referenced in a system? */
  def categoryReferencesCt(categoryName: String): Int = {
    val v = waitFor(
      db.run(
        sql"""select COUNT(DISTINCT A.ID) from "SYSTEM_OBJECT" A, PRIVACY_DECLARATION B where A.ORGANIZATION_ID = 1 AND
           B.SYSTEM_ID = A.ID AND JSON_OVERLAPS('["#$categoryName"]',B.data_categories) > 0""".as[Int]
      )
    )
    v.head
  }

  test(s"System.fidesKey must be unique") {
    testInsertConstraint({ sys: SystemObject => this.generator.sample.get.copy(fidesKey = sys.fidesKey) })
  }

  test("test parse-from-db json field errors") {
    val s              = SystemObjectGen.sample.get.copy(privacyDeclarations = None)
    val toInsertable   = SystemObject.toInsertable(s).get
    val fromInsertable = SystemObject.fromInsertable(toInsertable)
    s shouldEqual fromInsertable

    /* trying to parse a value where the input is invalid json fails.*/
    assertThrows[InvalidDataException] { SystemObject.fromInsertable(toInsertable.copy(_10 = "[Not valid json")) }
  }

  test("search for category string") {
    val dataCategory = "customer_content_data"
    val ct           = categoryReferencesCt(dataCategory)
    waitFor(
      service.create(
        generator.sample.get
          .copy(privacyDeclarations =
            Some(
              Seq(
                PrivacyDeclaration(
                  0L,
                  0L,
                  "test",
                  Set("customer_content_data"),
                  "provide",
                  "identified_data",
                  Set(),
                  Set()
                )
              )
            )
          ),
        requestContext
      )
    )

    val ct2: Int = categoryReferencesCt(dataCategory)
    ct2 should be > ct
  }
}
