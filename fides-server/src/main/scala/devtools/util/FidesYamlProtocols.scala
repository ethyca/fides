package devtools.util

import com.typesafe.scalalogging.LazyLogging
import devtools.domain._
import devtools.domain.enums._
import devtools.domain.policy.{PrivacyDeclaration, Policy, PolicyRule}
import net.jcazevedo.moultingyaml.{
  DefaultYamlProtocol,
  YamlArray,
  YamlBoolean,
  YamlDate,
  YamlFormat,
  YamlNaN,
  YamlNegativeInf,
  YamlNull,
  YamlNumber,
  YamlObject,
  YamlPositiveInf,
  YamlSet,
  YamlString,
  YamlValue
}
import org.joda.time.DateTime
import org.json4s.JValue

import java.sql.Timestamp
object FidesYamlProtocols extends DefaultYamlProtocol with LazyLogging {
  implicit val JValueFormat: YamlFormat[JValue] = new YamlFormat[JValue] {
    def write(r: JValue): YamlValue   = JsonSupport.toYaml(r)
    def read(yaml: YamlValue): JValue = YamlSupport.toJson(yaml)
  }

  implicit val MapAnyFormat: YamlFormat[Map[String, Any]] = new YamlFormat[Map[String, Any]] {
    def write(r: Map[String, Any]): YamlValue   = AnyFormat.write(r)
    def read(yaml: YamlValue): Map[String, Any] = AnyFormat.read(yaml).asInstanceOf[Map[String, Any]]
  }

  def yamlCustomMapKeyFormat[T](f: String => T): YamlFormat[Map[T, Any]] =
    new YamlFormat[Map[T, Any]] {
      def write(r: Map[T, Any]): YamlValue   = MapAnyFormat.write(r.map(t => t._1.toString -> t._2))
      def read(yaml: YamlValue): Map[T, Any] = MapAnyFormat.read(yaml).map(t => f(t._1) -> t._2)
    }

  implicit val TimestampFormat: YamlFormat[Timestamp] = new YamlFormat[Timestamp] {
    def write(r: Timestamp): YamlValue = YamlNumber(r.getTime)
    def read(yaml: YamlValue): Timestamp =
      yaml match {
        case y: YamlNumber => new Timestamp(y.value.longValue)
        case _             => null
      }
  }

  implicit val SetFormat: YamlFormat[Set[String]] = new YamlFormat[Set[String]] {
    override def write(obj: Set[String]): YamlValue = YamlSet(set = obj.map(s => YamlString(s)))

    override def read(yaml: YamlValue): Set[String] =
      yaml match {
        case YamlArray(a) =>
          a.map {
            case YamlString(s) => s
            case _             => null
          }.toSet.filter(x => x != null)
        case YamlSet(s) =>
          s.map {
            case YamlString(s) => s
            case _             => null
          }.filter(x => x != null)
        case _ => Set()
      }
  }
  implicit val AnyFormat: YamlFormat[Any] = new YamlFormat[Any] {

    def write(r: Any): YamlValue =
      r match {
        case x: String => YamlString(x)
        case x: Map[_, _] =>
          val filtered = x.toMap
          new YamlObject(filtered.map(t => (write(t._1), write(t._2))))

        case x: Seq[_]     => new YamlArray(x.filter(_ != None).map(write).toVector)
        case x: Int        => YamlNumber(x)
        case x: Long       => YamlNumber(x)
        case x: Double     => YamlNumber(x)
        case x: BigDecimal => YamlNumber(x)
        case x: BigInt     => YamlNumber(x)
        case null          => YamlNull
        case x: Boolean    => YamlBoolean(x)
        case x: DateTime   => YamlDate(x)
        case x: Set[_]     => YamlSet(x map write)
      }

    def read(yaml: YamlValue): Any = {
      yaml match {
        case YamlNumber(n)   => n
        case YamlString(s)   => s
        case YamlArray(l)    => l.map(v => read(v))
        case YamlBoolean(b)  => b
        case YamlObject(m)   => m.map { case (k: YamlValue, v: YamlValue) => (read(k), read(v)) }
        case YamlNull        => null
        case YamlDate(d)     => d
        case YamlNaN         => Double.NaN
        case YamlNegativeInf => Double.NegativeInfinity
        case YamlPositiveInf => Double.PositiveInfinity
        case YamlSet(s)      => s.map(v => read(v))
      }
    }
  }
  /* support for custom enum types.*/
  implicit val PolicyActionFormat: YamlFormat[PolicyAction]     = PolicyAction.yamlFormat
  implicit val InclusionFormat: YamlFormat[RuleInclusion]       = RuleInclusion.yamlFormat
  implicit val ApprovalStatusFormat: YamlFormat[ApprovalStatus] = ApprovalStatus.yamlFormat
  implicit val RoleFormat: YamlFormat[Role]                     = Role.yamlFormat
  implicit val AuditActionFormat: YamlFormat[AuditAction]       = AuditAction.yamlFormat
  implicit val ApprovalStatusMapFormat: YamlFormat[Map[ApprovalStatus, Any]] =
    yamlCustomMapKeyFormat[ApprovalStatus](t => ApprovalStatus.fromString(t).get)

  /** A YAML reader that can be configured to substitute in for missing values.
    * This is necessary when we're ingesting values that are missing required members (e.g. id value).
    * The writeMap values are appended to the input values, if they are not provided.
    */
  def withOptionalValues[T](values: Map[String, Any], baseFormatter: YamlFormat[T]): YamlFormat[T] =
    new YamlFormat[T] {
      import YamlSupport.yamlObjectToMergeable

      def write(r: T): YamlValue = baseFormatter.write(r)
      def read(yaml: YamlValue): T = {
        baseFormatter.read(yaml.asYamlObject().mergeAfter(values))
      }
    }
  def withOptionalLongId[T](baseFormatter: YamlFormat[T]): YamlFormat[T] =
    withOptionalValues(Map("id" -> 0L), baseFormatter)

  implicit val DeclarationFormat: YamlFormat[PrivacyDeclaration] = yamlFormat6(PrivacyDeclaration.apply)

  /* policy rule structures */
  implicit val PolicyRuleAspectGroupingFormat: YamlFormat[PolicyValueGrouping] = yamlFormat2(PolicyValueGrouping)

  /* domain objects */
  implicit val UserFormat: YamlFormat[User]              = withOptionalLongId[User](yamlFormat9(User.apply))
  implicit lazy val ApprovalFormat: YamlFormat[Approval] = withOptionalLongId[Approval](yamlFormat12(Approval.apply))
  implicit val AuditLogFormat: YamlFormat[AuditLog]      = withOptionalLongId[AuditLog](yamlFormat11(AuditLog.apply))
  implicit val DataQualifierFormat: YamlFormat[DataQualifier] =
    withOptionalLongId[DataQualifier](yamlFormat7(DataQualifier.apply))
  implicit val DataUseFormat: YamlFormat[DataUse] = withOptionalLongId[DataUse](yamlFormat7(DataUse.apply))
  implicit val SubjectCategoryFormat: YamlFormat[DataSubject] =
    withOptionalLongId[DataSubject](yamlFormat6(DataSubject.apply))
  implicit val DataCategoryFormat: YamlFormat[DataCategory] =
    withOptionalLongId[DataCategory](yamlFormat7(DataCategory.apply))
  implicit val SystemObjectFormat: YamlFormat[SystemObject] =
    withOptionalLongId[SystemObject](yamlFormat13(SystemObject.apply))
  implicit val RegistryFormat: YamlFormat[Registry] = withOptionalLongId[Registry](yamlFormat10(Registry.apply))
  implicit val OrganizationFormat: YamlFormat[Organization] =
    withOptionalLongId[Organization](yamlFormat7(Organization.apply))

  implicit val PolicyRuleFormat: YamlFormat[PolicyRule] =
    withOptionalValues[PolicyRule](Map("id" -> 0L, "policyId" -> 0L), yamlFormat13(PolicyRule.apply))
  implicit val PolicyFormat: YamlFormat[Policy] = withOptionalLongId[Policy](yamlFormat9(Policy.apply))
  implicit val DatasetFieldFormat: YamlFormat[DatasetField] =
    withOptionalValues[DatasetField](Map("id" -> 0L, "datasetId" -> 0L), yamlFormat9(DatasetField.apply))
  implicit val DatasetFormat: YamlFormat[Dataset] = withOptionalLongId[Dataset](yamlFormat14(Dataset.apply))

}
