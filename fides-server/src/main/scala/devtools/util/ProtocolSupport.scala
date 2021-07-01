package devtools.util

import com.typesafe.scalalogging.LazyLogging
import devtools.domain.DatasetField
import devtools.domain.enums._
import devtools.domain.policy.PolicyRule
import devtools.exceptions.InvalidDataException
import net.jcazevedo.moultingyaml.{
  YamlArray,
  YamlBoolean,
  YamlNull,
  YamlNumber,
  YamlObject,
  YamlSet,
  YamlString,
  YamlValue
}
import org.json4s.JsonAST.JString
import org.json4s.jackson.JsonMethods._
import org.json4s.jackson.Serialization
import org.json4s.native.Serialization.writePretty
import org.json4s.{CustomSerializer, _}

import scala.annotation.tailrec
import scala.util.{Failure, Success, Try}

object JsonSupport extends LazyLogging {

  /** Generate a serializer that will handle missing values as provided in the jObject.
    *
    * This is especially useful for ingesting values that don't have a (mandatory) id (which
    * needs to be provided for by the platform).
    */

  def withMapValues[T](m: JObject, formats: Formats)(implicit manifest: Manifest[T]): CustomSerializer[T] = {
    new CustomSerializer[T](_ =>
      (
        {
          case i: JObject =>
            val v: JObject = m merge i // this ensures that values in i take precedence over default values in m
            v.extract[T](formats, manifest)

        },
        {
          case f: T => Extraction.decompose(f)(formats)
        }
      )
    )
  }

  import org.json4s.JsonDSL._

  implicit val datasetFieldFormat: CustomSerializer[DatasetField] =
    withMapValues[DatasetField](("id" -> 0L) ~ ("datasetTableId" -> 0L), DefaultFormats)
  implicit val policyRuleFormat: CustomSerializer[PolicyRule] = withMapValues[PolicyRule](
    ("id" -> 0L) ~ ("policyId" -> 0L),
    DefaultFormats + RuleInclusion.jsonFormat + PolicyAction.jsonFormat
  )

  implicit lazy val formats: Formats = DefaultFormats +
    ApprovalStatus.jsonFormat +
    Role.jsonFormat +
    PolicyAction.jsonFormat +
    RuleInclusion.jsonFormat +
    AuditAction.jsonFormat +
    ApprovalStatus.keySerializer +
    datasetFieldFormat +
    policyRuleFormat

  /** extract an optionally present nested value. */
  @tailrec
  def extractNested[T](j: JValue, keys: String*)(implicit manifest: Manifest[T]): T =
    keys match {
      case Seq() => j.extract[T]

      case Seq(s, rest @ _*) =>
        j \ s match {
          case inner: JValue => extractNested(inner, rest: _*)
        }
    }

  /** String -> T */
  def parseToObj[T](s: String)(implicit formats: Formats = formats, manifest: Manifest[T]): Try[T] =
    loads(s) map { j => j.extract[T] }

  /** T -> String */
  def dumps[T <: AnyRef](t: T): String = Serialization.write(t)(formats)

  /** String -> Json */
  def loads(s: String): Try[JValue] =
    try {
      Success(parse(s))
    } catch {
      case e: Throwable => Failure(InvalidDataException(e.getMessage))
    }

  /** Json -> formatted string */
  def prettyPrint(j: JValue): String = writePretty(j)

  /** T -> Json */
  def toAST[T <: AnyRef](t: T): JValue = Extraction.decompose(t)

  /** Json -> T */
  def fromAST[T](j: JValue)(implicit manifest: Manifest[T]): Try[T] = {
    try {
      Success(j.extract[T])
    } catch {
      case e: Throwable =>
        Failure(
          InvalidDataException(
            s"Could not extractAny value of type ${manifest.runtimeClass.getSimpleName} from ${dumps(j)}:${e.getMessage
              .replace('\n', ':')}"
          )
        )
    }
  }

  /** Json -> YAML */
  def toYaml(j: JValue): YamlValue = {
    j match {
      case JNothing    => YamlNull
      case JNull       => YamlNull
      case JString(s)  => YamlString(s)
      case JInt(i)     => YamlNumber(i)
      case JLong(l)    => YamlNumber(l)
      case JDouble(d)  => YamlNumber(d)
      case JDecimal(d) => YamlNumber(d)
      case JBool(b)    => YamlBoolean(b)
      case JSet(s)     => YamlSet(s.map(toYaml))
      case JArray(s)   => YamlArray(s.map(toYaml).toVector)
      case JObject(o) =>
        val v: Seq[(YamlString, YamlValue)] = o map { t => (YamlString(t._1), toYaml(t._2)) }
        YamlObject(v: _*)
    }
  }

  /** Generate a report of differences from left -> right by key association:
    *
    *  changed: Values with same key but altered values
    *  added: keys in right but not in left
    *  deleted: keys in left but not in right
    */
  def difference(left: JValue, right: JValue): JsonAST.JObject = {
    val Diff(changed, added, deleted) = left diff right // JsonSupport.toAST[T](left) diff JsonSupport.toAST[T](right)
    ("changed" -> changed) ~ ("added" -> added) ~ ("deleted" -> deleted)
  }
}

import net.jcazevedo.moultingyaml._

object YamlSupport {

  /** Parse as a generic map or list. This will support parseToObj(Map[String,Any]), which the basic
    * yaml parser will not.
    */
  def parseToObj[T](s: String)(implicit reader: YamlReader[T]): Try[T] =
    loads(s).flatMap(y => fromAST[T](y))

  def loads(s: String): Try[YamlValue] =
    Try {
      s.parseYaml()
    }

  /** Yaml -> string */
  def dumps(y: YamlValue): String = y.prettyPrint

  /** T -> YAML */
  def toAST[T](t: T)(implicit writer: YamlWriter[T]): YamlValue = t.toYaml

  /** YAML -> T */
  def fromAST[T](y: YamlValue)(implicit reader: YamlReader[T]): Try[T] =
    try {
      Success(y.convertTo[T])
    } catch {
      case e: Exception => Failure(e)
    }

  def extractAny(yaml: YamlValue): Any = FidesYamlProtocols.AnyFormat.read(yaml)

  @tailrec
  def extractNested[T](yaml: YamlValue, keys: String*)(implicit reader: YamlReader[T]): Try[T] =
    keys match {
      case Seq() => fromAST[T](yaml)
      case Seq(s, rest @ _*) =>
        yaml.asYamlObject.getFields(YamlString(s)) match {
          case Seq(o: YamlValue) => extractNested(o, rest: _*)
        }
    }

  /** YAML -> Json */
  def toJson(yaml: YamlValue): JValue = {
    yaml match {
      case YamlNumber(n) =>
        if (n.isValidInt) {
          JInt(n.toInt)
        } else if (n.isValidLong) {
          JLong(n.toLong)
        } else if (n.isDecimalDouble) {
          JDouble(n.toDouble)
        } else {
          JDecimal(n)
        }
      case YamlString(s)  => JString(s)
      case YamlArray(l)   => JArray(l.map(y => toJson(y)).toList)
      case YamlBoolean(b) => JBool(b)
      case YamlObject(m: Map[YamlValue, YamlValue]) =>
        val v: Map[String, _root_.org.json4s.JsonAST.JValue] = m.map { t =>
          JField(extractAny(t._1).toString, toJson(t._2))
        }
        JObject(v.toList)
      case YamlNull        => JNull
      case YamlDate(d)     => JLong(d.getMillis)
      case YamlNaN         => JDouble(Double.NaN)
      case YamlNegativeInf => JDouble(Double.NegativeInfinity)
      case YamlPositiveInf => JDouble(Double.PositiveInfinity)
      case YamlSet(s)      => JSet(s.map(v => toJson(v)))
    }
  }

  import scala.language.implicitConversions

  /** Used to allow merging of yaml objects with arbitrary maps. */
  implicit def yamlObjectToMergeable(y: YamlObject): MergeableYamlObject = MergeableYamlObject(y)

  final case class MergeableYamlObject(y: YamlObject) {
    /** Merge in other map, values in other map take precedence */
    def mergeBefore(other: Map[String, Any]): YamlObject = {
      val combined = FidesYamlProtocols.MapAnyFormat.read(y) ++ other
      FidesYamlProtocols.MapAnyFormat.write(combined).asYamlObject()
    }

    /** Merge in other map, values in this object take precedence */
    def mergeAfter(other: Map[String, Any]): YamlObject = {
      val combined = other ++ FidesYamlProtocols.MapAnyFormat.read(y)
      FidesYamlProtocols.MapAnyFormat.write(combined).asYamlObject()
    }

  }
}
