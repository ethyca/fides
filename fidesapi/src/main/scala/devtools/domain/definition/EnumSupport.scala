package devtools.domain.definition

import devtools.exceptions.{InvalidDataException, NoSuchValueException}
import devtools.util.YamlSupport
import net.jcazevedo.moultingyaml.{YamlFormat, YamlString, YamlValue}
import org.json4s.JsonAST.JString
import org.json4s.{CustomSerializer, Formats, KeySerializer, TypeInfo}

import scala.util.{Failure, Success, Try}

/** Common behavior for custom defined enum types */
abstract class EnumSupport[T](implicit val manifest: Manifest[T]) {

  def values: Set[T]

  def valueMap: Map[String, T] = values.map(t => (t.toString.toLowerCase(), t)).toMap

  def keys: Set[String] = valueMap.keySet

  val typeName: String = manifest.runtimeClass.getSimpleName

  def isValid(s: String): Boolean = s != null && keys.contains(s.toLowerCase())

  def fromString(s: String): Try[T] = {
    valueMap.get(s.toLowerCase) match {
      case Some(v) => Success(v)
      case None    => Failure(NoSuchValueException(typeName, s))
    }
  }

  /** Yaml serializer support. See [[devtools.util.FidesYamlProtocols]] */
  def yamlFormat: YamlFormat[T] =
    new YamlFormat[T] {
      def write(r: T): YamlValue = YamlString(r.toString)

      def read(y: YamlValue): T = fromString(YamlSupport.extractAny(y).toString).get
    }

  /** Json serializer support. See [[devtools.util.JsonSupport]] */
  def jsonFormat: CustomSerializer[T] =
    new CustomSerializer[T](_ =>
      (
        {
          case JString(s) => fromString(s).get
        },
        {
          case x: T => JString(x.toString)
        }
      )
    )

  /** Json serializer required for use of an EnumSupport type as a map key. */
  def keySerializer: KeySerializer[T] =
    new KeySerializer[T] {

      def deserialize(implicit format: Formats): PartialFunction[(TypeInfo, String), T] = {
        case (t, s) if t.clazz == manifest.runtimeClass => fromString(s).get
      }

      def serialize(implicit format: Formats): PartialFunction[Any, String] = {
        case t => t.toString
      }
    }

  /** Verify that this value is a legal enum member. Return the original value
    * Throw an InvalidDataException if the value is illegal
    */
  def verified(s: String): String = {
    if (isValid(s)) s
    else throw InvalidDataException(s"$s is not a valid ${manifest.runtimeClass.getSimpleName}")
  }
}
