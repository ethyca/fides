package devtools

import com.typesafe.scalalogging.LazyLogging
import devtools.Generators.{SystemObjectGen, _}
import devtools.controller.RequestContext
import devtools.controller.definition.ApiResponse
import devtools.domain._
import devtools.domain.enums._
import devtools.domain.policy.{Policy, PolicyRule}
import devtools.persist.dao.OrganizationDAO
import devtools.util.JsonSupport.{parseToObj => jParseToObj}
import devtools.util.Sanitization.sanitizeUniqueIdentifier
import devtools.util.{JsonSupport, JwtUtil, Pagination, waitFor}
import org.json4s.Formats
import org.scalacheck.Gen
import org.scalatest.matchers.{MatchResult, Matcher}

import java.sql.Timestamp
import scala.collection.Seq
import scala.concurrent.{ExecutionContextExecutor, Future}
import scala.io.Source
import scala.util.matching.Regex
import scala.util.{Random, Try}

trait TestUtils extends LazyLogging {

  implicit val executionContext: ExecutionContextExecutor = App.executionContext

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

  def systemOf(fidesKeyName: String, declarations: PrivacyDeclaration*): SystemObject =
    SystemObjectGen.sample.get.copy(fidesKey = fidesKeyName, privacyDeclarations = Some(declarations))

  def auditLogOf(objectId: Long, action: AuditAction, typeName: String): AuditLog =
    AuditLog(0L, objectId, 1, None, 1, action, typeName, None, None, None, None)

  def datasetOf(name: String, fields: DatasetField*): Dataset =
    Dataset(0L, 1L, name, None, None, None, None, None, None, None, None, Some(fields), None, None)

  def datasetFieldOf(name: String): DatasetField =
    DatasetField(
      0L,
      0L,
      name,
      Some("path"),
      None,
      Some(smallSetOf(0, 5, availableDataCategories)),
      Some(oneOf(availableDataQualifiers)),
      None,
      None
    )

  def datasetOf(
    dataQualifier: Option[DataQualifierName],
    dataCategories: Option[Set[DataCategoryName]],
    fields: DatasetField*
  ): Dataset =
    Dataset(0L, 1L, "a", None, None, None, None, dataCategories, dataQualifier, None, None, Some(fields), None, None)

  def datasetFieldOf(
    name: String,
    dataQualifier: DataQualifierName,
    dataCategories: Set[DataCategoryName]
  ): DatasetField =
    DatasetField(
      0L,
      0L,
      name,
      None,
      None,
      Some(dataCategories),
      Some(dataQualifier),
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

  def findAuditLogs(objectId: Long, typeName: String, action: AuditAction): Future[Seq[AuditLog]] = {
    import slick.jdbc.MySQLProfile.api._
    App.auditLogDAO.filter(a => a.objectId === objectId && a.typeName === typeName && a.action === action.toString)
  }
}

object Generators {

  def versionStamp: Option[Long]           = Some(Math.abs(Random.nextLong()))
  val availableDataQualifiers: Seq[String] = App.dataQualifierDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDataUses: Seq[String]       = App.dataUseDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDataCategories: Seq[String] = App.dataCategoryDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  val availableDataSubjects: Seq[String]   = App.dataSubjectDAO.cacheGetAll(1).values.map(_.fidesKey).toSeq
  lazy val availableDatasets: Seq[String] =
    waitFor(App.datasetDAO.findAllInOrganization(1, Pagination.unlimited)).map(_.fidesKey)
  val availableDatasetsOrFields: Seq[String] = Seq(
    "test_dataset",
    "test_dataset.field1",
    "test_dataset.field2",
    "test_dataset2",
    "test_dataset2.field1",
    "test_dataset2.field2"
  )

  val genName: Gen[String]     = Gen.resultOf { _: Int => faker.Name.first_name }
  val genLongName: Gen[String] = Gen.resultOf { _: Int => faker.Name.name }
  def fidesKey: String         = sanitizeUniqueIdentifier(faker.Name.name + "_" + faker.Name.name)

  def randomText(): String = faker.Lorem.sentence()
  def blankSystem: SystemObject =
    SystemObject(
      0L,
      1L,
      None,
      fidesKey,
      None,
      None,
      None,
      None,
      Some("DATABASE"),
      None,
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
      id        <- Gen.posNum[Long]
      objectId  <- Gen.posNum[Long] //TODO system in test org
      userId    <- Gen.posNum[Long] //TODO user in test org
      status    <- Gen.oneOf(ApprovalStatus.values)
      actionStr <- Gen.oneOf(Seq("rate", "create", "update"))
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
      id             <- Gen.posNum[Long]
      datasetTableId <- Gen.posNum[Long]
      name           <- genLongName
      dataQualifier  <- Gen.option(Gen.oneOf(availableDataQualifiers))
    } yield DatasetField(
      id,
      datasetTableId,
      name,
      Some("path"),
      Some(randomText()),
      Some(smallSetOf(1, 4, availableDataCategories)),
      dataQualifier,
      timestamp(),
      timestamp()
    )

  val DatasetGen: Gen[Dataset] =
    for {
      id            <- Gen.posNum[Long]
      name          <- Gen.option(genLongName)
      loc           <- Gen.option(genLongName)
      dtype         <- Gen.option(genLongName)
      dataQualifier <- Gen.option(Gen.oneOf(availableDataQualifiers))
      fields        <- Gen.option(smallListGen(2, 5, DatasetFieldGen))
    } yield Dataset(
      id,
      1L,
      fidesKey.replace('.', '_'),
      versionStamp,
      None,
      name,
      Some(randomText()),
      Some(smallSetOf(1, 4, availableDataCategories)),
      dataQualifier,
      loc,
      dtype,
      fields.map(_.toSeq),
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
  val DataSubjectGen: Gen[DataSubject] =
    for {
      id: Int <- Gen.posNum[Int]
      name    <- Gen.resultOf { _: Int => faker.Name.name }
    } yield DataSubject(id, None, 1, fidesKey, Some(name), Some(randomText()))
  val DeclarationGen: Gen[PrivacyDeclaration] =
    for {
      name      <- genName
      use       <- Gen.oneOf(availableDataUses)
      qualifier <- Gen.oneOf(availableDataQualifiers)
    } yield {

      val fields = smallSetOf(0, 4, availableDatasetsOrFields)

      PrivacyDeclaration(
        0L,
        0L,
        name,
        smallSetOf(1, 4, availableDataCategories),
        use,
        qualifier,
        smallSetOf(1, 4, availableDataSubjects),
        fields
      )
    }

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
      subjectCategories <- PolicyValueGroupingGenOf(availableDataSubjects)
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
      id   <- Gen.posNum[Long]
      name <- genName
    } yield Policy(id, 1, fidesKey, Some(0L), Some(name), Some(randomText()), None, timestamp(), timestamp())

  /** A Generated object that will pass validation checks. */
  import slick.jdbc.MySQLProfile.api._
  val SystemObjectGen: Gen[SystemObject] = {

    for {
      id: Long <- Gen.posNum[Long]
      name     <- Gen.option(genName)
      /* Require that the systemType value rateByRule one of [[devtools.domain.enums.SystemType]] */
      systemType   <- Gen.option(Gen.oneOf("Api", "Database", "Unknown"))
      declarations <- smallListGen(1, 4, DeclarationGen)
    } yield SystemObject(
      id,
      1,
      None,
      fidesKey,
      versionStamp,
      None,
      name,
      Some(randomText()),
      systemType,
      Some(declarations.toList),
      Random.shuffle(
        waitFor(App.systemDAO.filter(_.organizationId === 1L)).map(_.fidesKey).take(Random.nextInt(4)).toSet
      ),
      timestamp(),
      timestamp()
    )
  }

  val RegistryGen: Gen[Registry] = {
    for {
      id   <- Gen.posNum[Long]
      name <- Gen.option(genName)
    } yield Registry(id, 1, fidesKey, versionStamp, None, name, Some(randomText()), None, timestamp(), timestamp())
  }

  val UserGen: Gen[User] = for {
    id        <- Gen.posNum[Int]
    userName  <- genName
    firstName <- Gen.option(genName)
    lastName  <- Gen.option(Gen.resultOf { _: Int => faker.Name.last_name })
    role      <- Gen.oneOf(Role.values)
  } yield User(id, 1, userName, firstName, lastName, role, Some(JwtUtil.generateToken()), timestamp(), timestamp())
  val requestContext: RequestContext = RequestContext(UserGen.sample.get.copy(id = 1, organizationId = 1))

  private def domainObjectGenerators: Seq[Gen[_ <: AnyRef]] =
    Seq(
      ApprovalGen,
      DataCategoryGen,
      DataQualifierGen,
      DataSubjectGen,
      DataUseGen,
      DeclarationGen,
      OrgGen,
      PolicyRuleGen,
      PolicyGen,
      SystemObjectGen,
      RegistryGen,
      UserGen,
      DatasetGen,
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
