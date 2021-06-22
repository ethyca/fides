package devtools

import devtools.Generators.{SystemObjectGen, _}
import devtools.controller.RequestContext
import devtools.controller.definition.ApiResponse
import devtools.domain._
import devtools.domain.enums._
import devtools.domain.policy.{Declaration, Policy, PolicyRule}
import devtools.persist.dao.OrganizationDAO
import devtools.util.JsonSupport.{parseToObj => jParseToObj}
import devtools.util.Sanitization.sanitizeUniqueIdentifier
import devtools.util.{JsonSupport, waitFor}
import org.json4s.Formats
import org.scalacheck.Gen
import org.scalatest.matchers.{MatchResult, Matcher}

import java.sql.Timestamp
import scala.collection.Seq
import scala.io.Source
import scala.util.matching.Regex
import scala.util.{Random, Try}

trait TestUtils {

  def randomInt: Int = Random.nextInt()

  def randomLong: Long = Random.nextLong()

  def readFile(filename: String): String = Source.fromResource(filename).getLines().mkString("\n")

  def parseBody[T](body: String)(implicit manifest: Manifest[T]): Try[T] =
    jParseToObj[ApiResponse[T]](body).map(_.data.get)

  def toMap[T <: AnyRef](t: T): Map[String, Any] =
    try {
      jParseToObj[Map[String, Any]](JsonSupport.dumps(t)).get
    } catch {
      case e: Throwable => println(s"ERROR: $e .... $t"); e.printStackTrace(); throw e
    }

  def printTrace(str: String): Unit = {
    println(s"================TRACE $str===============")
    var s = ""
    Thread.currentThread().getStackTrace.foreach { t =>
      { println(s"$s\t${Thread.currentThread().getId}\t$t"); s += "-" }
    }
  }

  def policyRuleOf(
    cats: PolicyValueGrouping,
    uses: PolicyValueGrouping,
    qualifier: DataQualifierName,
    subjectCategories: PolicyValueGrouping,
    action: PolicyAction,
    name: String = fidesKey
  ): PolicyRule =
    PolicyRule(1, 1, 1, name, None, None, cats, uses, subjectCategories, Some(qualifier), action, None, None)

  def policyOf(fidesKeyName: String, rules: PolicyRule*): Policy =
    Policy(0, 1, fidesKeyName, None, None, None, Some(rules), None, None)

  def systemOf(fidesKeyName: String, declarations: Declaration*): SystemObject =
    SystemObjectGen.sample.get.copy(fidesKey = fidesKeyName, declarations = declarations)

  def datasetOf(name: String, tables: DatasetTable*): Dataset =
    Dataset(0, 1, name, None, None, None, None, None, Some(tables), None, None)

  def datasetTableOf(name: String, fields: DatasetField*): DatasetTable =
    DatasetTable(0, 0, name, None, Some(fields), None, None)

  def datasetFieldOf(name: String): DatasetField =
    DatasetField(
      0,
      0,
      name,
      None,
      Some(smallSetOf(0, 5, availableDataCategories)),
      Some(oneOf(availableDataQualifiers)),
      None,
      None
    )

  class ContainsErrorStringMatcher(pattern: String) extends Matcher[Seq[String]] {
    def apply(strings: Seq[String]): MatchResult = {
      val r = new Regex(pattern).unanchored
      MatchResult(
        strings.exists(s => r.findFirstMatchIn(s).isDefined),
        s"Strings [${strings.mkString(",")}] did not contain pattern $pattern",
        s"Strings matched pattern $pattern"
      )
    }
  }
  implicit val formats: Formats = JsonSupport.formats

  def prettyPrintJson[T <: AnyRef](s: T): Unit = println(JsonSupport.prettyPrint(JsonSupport.toAST[T](s)))

  def containMatchString(pattern: String): ContainsErrorStringMatcher = new ContainsErrorStringMatcher(pattern)
  private val organizationDAO: OrganizationDAO                        = App.organizationDAO
  def currentVersionStamp(organizationId: Int): Long                  = waitFor(organizationDAO.getVersion(organizationId)).get
}

object Generators {

  def versionStamp: Option[Long]              = Some(Math.abs(Random.nextLong()))
  val availableDataQualifiers: Seq[String]    = App.dataQualifierDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDataUses: Seq[String]          = App.dataUseDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDataCategories: Seq[String]    = App.dataCategoryDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableSubjectCategories: Seq[String] = App.dataSubjectCategoryDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDatasets: Seq[String]          = waitFor(App.datasetDAO.findAllInOrganization(1)).map(_.fidesKey)
  val genName: Gen[String]                    = Gen.resultOf { _: Int => faker.Name.first_name }
  val genLongName: Gen[String]                = Gen.resultOf { _: Int => faker.Name.name }
  def fidesKey: String                        = sanitizeUniqueIdentifier(faker.Name.name + "_" + faker.Name.name)

  def randomText(): String = faker.Lorem.sentence()
  def blankSystem: SystemObject =
    SystemObject(
      0,
      1,
      None,
      fidesKey,
      None,
      Some("DATABASE"),
      None,
      None,
      scala.Seq[Declaration](),
      Set(),
      Set(),
      None,
      None
    )

  def smallListGen[T](min: Int, max: Int, gen: Gen[T]): Gen[Seq[T]] = Gen.listOfN(Random.nextInt(max + min) + min, gen)

  def smallSetOf[T](min: Int, max: Int, seq: Seq[T]): Set[T] = {
    val t = min + Math.max(0, Random.nextInt(max - min + 1))
    Random.shuffle(seq).take(t).toSet
  }

  def oneOf[T](seq: Seq[T]): T = Random.shuffle(seq).take(1).head

  /* set nanos to 0 because default json rendering can round them out and throw off equality tests.*/
  def timestamp(): Option[Timestamp] = {
    val t = new Timestamp(math.abs(Random.nextInt).longValue + System.currentTimeMillis())
    t.setNanos(0)
    Some(t)
  }

  val genVersionString: Gen[String] = for {
    n <- Gen.someOf(1 to 5)
  } yield n.map(_.toString).mkString(".")

  val ApprovalGen: Gen[Approval] =
    for {
      id        <- Gen.posNum[Int]
      objectId  <- Gen.posNum[Int] //TODO system in test org
      userId    <- Gen.posNum[Int] //TODO user in test org
      status    <- Gen.oneOf(ApprovalStatus.values)
      actionStr <- Gen.oneOf(Seq("rate", "create", "update"))
      errors    <- smallListGen[String](1, 3, genName)
      warnings  <- smallListGen[String](1, 3, genName)
    } yield Approval(
      id,
      1,
      Some(objectId),
      None,
      userId,
      versionStamp,
      Some(Random.nextLong().toHexString),
      Some(s"commit message"),
      actionStr,
      status,
      Some(Map()),
      timestamp()
    )

  val DataCategoryGen: Gen[DataCategory] =
    for {
      id: Int <- Gen.posNum[Int]
      clause  <- Gen.option(genVersionString)
      name    <- genLongName
    } yield DataCategory(id, None, 1, fidesKey, Some(name), clause, Some(randomText()))
  /*
    Dataset types
   */
  val DatasetFieldGen: Gen[DatasetField] =
    for {
      id             <- Gen.posNum[Int]
      datasetTableId <- Gen.posNum[Int]
      name           <- genLongName
      dataQualifier  <- Gen.option(Gen.oneOf(availableDataQualifiers))
    } yield DatasetField(
      id,
      datasetTableId,
      name,
      Some(randomText()),
      Some(smallSetOf(1, 4, availableDataCategories)),
      dataQualifier,
      timestamp(),
      timestamp()
    )
  val DatasetTableGen: Gen[DatasetTable] =
    for {
      id: Int   <- Gen.posNum[Int]
      datasetId <- Gen.posNum[Int]
      name      <- genLongName
      fields    <- Gen.option(smallListGen(2, 5, DatasetFieldGen))
    } yield DatasetTable(
      id,
      datasetId,
      name,
      Some(randomText()),
      fields.map(_.toSeq),
      timestamp(),
      timestamp()
    )

  val DatasetGen: Gen[Dataset] =
    for {
      id: Int <- Gen.posNum[Int]
      name    <- Gen.option(genLongName)
      loc     <- Gen.option(genLongName)
      dtype   <- Gen.option(genLongName)
      tables  <- Gen.option(smallListGen(2, 5, DatasetTableGen))
    } yield Dataset(
      id,
      1,
      fidesKey,
      versionStamp,
      name,
      Some(randomText()),
      loc,
      dtype,
      tables.map(_.toSeq),
      timestamp(),
      timestamp()
    )

  /*
  Taxonomy types
   */
  val DataUseGen: Gen[DataUse] =
    for {
      id: Int <- Gen.posNum[Int]
      clause  <- Gen.option(genVersionString)
      name    <- genName
    } yield DataUse(id, None, 1, fidesKey, Some(name), clause, Some(randomText()))

  val DataQualifierGen: Gen[DataQualifier] =
    for {
      id: Int <- Gen.posNum[Int]
      clause  <- Gen.option(genVersionString)
      name    <- Gen.resultOf { _: Int => faker.Name.name }
    } yield DataQualifier(id, None, 1, fidesKey, Some(name), clause, Some(randomText()))
  val DataSubjectCategoryGen: Gen[DataSubjectCategory] =
    for {
      id: Int <- Gen.posNum[Int]
      name    <- Gen.resultOf { _: Int => faker.Name.name }
    } yield DataSubjectCategory(id, None, 1, fidesKey, Some(name), Some(randomText()))
  val DeclarationGen: Gen[Declaration] =
    for {
      name      <- genName
      use       <- Gen.oneOf(availableDataUses)
      qualifier <- Gen.oneOf(availableDataQualifiers)
    } yield Declaration(
      name,
      smallSetOf(1, 4, availableDataCategories),
      use,
      qualifier,
      smallSetOf(1, 4, availableSubjectCategories)
    )
  val OrgGen: Gen[Organization] =
    for {
      id          <- Gen.posNum[Int]
      description <- Gen.oneOf(None, Some(randomText()))
    } yield Organization(id, fidesKey, versionStamp, Some(faker.Company.name), description, timestamp(), timestamp())

  def PolicyValueGroupingGenOf(seq: Seq[String]): Gen[PolicyValueGrouping] =
    for {
      t <- Gen.oneOf(RuleInclusion.values)
    } yield PolicyValueGrouping(t, smallSetOf(1, 4, seq))

  val PolicyRuleGen: Gen[PolicyRule] =
    for {
      id                <- Gen.posNum[Int]
      name              <- genName
      dataCategory      <- PolicyValueGroupingGenOf(availableDataCategories)
      dataQualifier     <- Gen.option(Gen.oneOf(availableDataQualifiers))
      dataUses          <- PolicyValueGroupingGenOf(availableDataUses)
      subjectCategories <- PolicyValueGroupingGenOf(availableSubjectCategories)
      action            <- Gen.oneOf(PolicyAction.values)
    } yield {
      PolicyRule(
        id,
        1,
        1,
        name,
        None,
        Some(randomText()),
        dataCategory,
        dataUses,
        subjectCategories,
        dataQualifier,
        action,
        timestamp(),
        timestamp()
      )
    }

  val PolicyGen: Gen[Policy] =
    for {
      id   <- Gen.posNum[Int]
      name <- genName
    } yield Policy(id, 1, fidesKey, Some(0L), Some(name), Some(randomText()), None, timestamp(), timestamp())

  /** A Generated object that will pass validation checks. */
  import slick.jdbc.MySQLProfile.api._
  val SystemObjectGen: Gen[SystemObject] = {

    for {
      id: Int <- Gen.posNum[Int]
      name    <- Gen.option(genName)
      /* Require that the systemType value rateByRule one of [[devtools.domain.enums.SystemType]] */
      fidesSystemType <- Gen.option(Gen.oneOf("Api", "Database", "Unknown"))
      declarations    <- smallListGen(1, 4, DeclarationGen)
    } yield SystemObject(
      id,
      1,
      None,
      fidesKey,
      versionStamp,
      fidesSystemType,
      name,
      Some(randomText()),
      declarations.toList,
      Random.shuffle(
        waitFor(App.systemDAO.filter(_.organizationId === 1L)).map(_.fidesKey).take(Random.nextInt(4)).toSet
      ),
      smallSetOf(0, 4, availableDatasets),
      timestamp(),
      timestamp()
    )
  }

  val RegistryGen: Gen[Registry] = {
    for {
      id   <- Gen.posNum[Long]
      name <- Gen.option(genName)
    } yield Registry(id, 1, fidesKey, versionStamp, name, Some(randomText()), None, timestamp(), timestamp())
  }

  val UserGen: Gen[User] = for {
    id        <- Gen.posNum[Int]
    userName  <- genName
    firstName <- Gen.option(genName)
    lastName  <- Gen.option(Gen.resultOf { _: Int => faker.Name.last_name })
    role      <- Gen.oneOf(Role.values)
  } yield User(id, 1, userName, firstName, lastName, role, timestamp(), timestamp())
  val requestContext: RequestContext = RequestContext(UserGen.sample.get.copy(id = 1, organizationId = 1))

  private def domainObjectGenerators: Seq[Gen[_ <: AnyRef]] =
    Seq(
      ApprovalGen,
      DataCategoryGen,
      DataQualifierGen,
      DataSubjectCategoryGen,
      DataUseGen,
      DeclarationGen,
      OrgGen,
      PolicyRuleGen,
      PolicyGen,
      SystemObjectGen,
      RegistryGen,
      UserGen,
      DatasetGen,
      DatasetTableGen,
      DatasetFieldGen
    )
  def main(args: Array[String]): Unit = {

    for (gen <- domainObjectGenerators) {
      val sample = gen.sample.get
      val json   = JsonSupport.prettyPrint(JsonSupport.toAST(sample))
      println(s"\n----${sample.getClass.getSimpleName}----\n$json\n\n")
    }
    println("\n\n===ENUMS===\n\n")

    val v = Seq(ApprovalStatus, AuditAction, PolicyAction, RuleInclusion, Role)
    v.foreach { e =>
      println(s"\n----${e.getClass.getSimpleName}----\n${e.values}")

    }

  }

}
