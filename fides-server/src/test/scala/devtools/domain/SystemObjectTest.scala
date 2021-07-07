package devtools.domain

import devtools.App
import devtools.Generators.SystemObjectGen
import devtools.exceptions.InvalidDataException
import devtools.util.{FidesYamlProtocols, waitFor}
import faker._
import org.scalatest.matchers.must.Matchers.be
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import java.sql.Timestamp

class SystemObjectTest
  extends DomainObjectTestBase[SystemObject, Long](
    App.systemService,
    SystemObjectGen,
    FidesYamlProtocols.SystemObjectFormat
  ) {
  private val dataCategoryDAO                                   = App.dataCategoryDAO
  override def editValue(t: SystemObject): SystemObject         = t.copy(fidesKey = Name.name)
  override def maskForComparison(t: SystemObject): SystemObject = t.copy(creationTime = None, lastUpdateTime = None)

  test(s"System.fidesKey must be unique") {
    testInsertConstraint({ sys: SystemObject => this.generator.sample.get.copy(fidesKey = sys.fidesKey) })
  }

  test("test parse-from-db json field errors") {
    val s              = SystemObjectGen.sample.get
    val toInsertable   = SystemObject.toInsertable(s).get
    val fromInsertable = SystemObject.fromInsertable(toInsertable)
    s shouldEqual fromInsertable

    /* trying to parse a value where the input is invalid json fails.*/
    assertThrows[InvalidDataException] { SystemObject.fromInsertable(toInsertable.copy(_10 = "[Not valid json")) }
  }

  test("search for category string") {
    val dataCategory = "customer_content_data"
    val ct: Long     = waitFor(App.systemDAO.runAction(dataCategoryDAO.categoryReferencesCtAction(dataCategory)))
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

    val ct2: Long = waitFor(App.systemDAO.runAction(dataCategoryDAO.categoryReferencesCtAction(dataCategory)))
    ct2 should be > ct
  }
}
