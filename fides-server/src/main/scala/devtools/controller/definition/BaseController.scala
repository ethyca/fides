package devtools.controller.definition

import devtools.controller.definition.ApiResponse.asyncResponse
import devtools.domain.definition.IdType
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.UserDAO
import devtools.persist.service.definition.Service
import devtools.util.YamlSupport._
import devtools.util.{JsonSupport, Pagination, YamlSupport}
import net.jcazevedo.moultingyaml.{YamlFormat, YamlObject, YamlReader, YamlValue}
import org.json4s.JValue
import org.json4s.JsonAST.JObject
import org.scalatra.swagger.Swagger

import scala.concurrent.ExecutionContext
import scala.util.{Failure, Try}

abstract class BaseController[T <: IdType[T, PK], PK](implicit
  val executor: ExecutionContext,
  val manifest: Manifest[T],
  val pkManifest: Manifest[PK]
) extends ControllerSupport with AuthenticationSupport {

  lazy val typeName: String               = manifest.runtimeClass.getSimpleName
  lazy val applicationDescription: String = s"$typeName API"
  val service: Service[T, PK]
  val userDAO: UserDAO
  val yamlFormat: YamlFormat[T]
  val swagger: Swagger
  def toPK(idStr: String): Try[PK]
  def inputMergeMap: Map[String, Any]

  def intParam(p: Option[String], default: Int): Int =
    p match {
      case Some(o) => Try(o.trim.toInt).getOrElse(default)
      case _       => default
    }

  /** Find all */
  get(
    "/",
    operation(
      apiOperation[List[T]](s"getAll${typeName}s")
        .summary(s"Show all ${typeName}s")
        .description(s"Shows all the ${typeName}s")
        .parameters(
          queryParam[String]("offset").description(s"optional pagination offset, default 0"),
          queryParam[String]("limit").description(s"optional pagination limit, default 100")
        )
    )
  ) {

    val offset = intParam(params.get("offset"), 0)
    val limit  = intParam(params.get("limit"), 100)

    params.get("search") match {
      case Some(search) => asyncResponse(service.search(search, requestContext, Pagination(limit, offset)))
      case _            => asyncResponse(service.getAll(requestContext, Pagination(limit, offset)))
    }
  }

  /** read content type from header, digest either as yaml or json. */
  def ingest(requestBody: String, contentTypeHeader: Option[String], merge: Map[String, Any] = Map()): Try[T] = {
    contentTypeHeader.map(_.toLowerCase) match {
      case Some("application/yaml") =>
        YamlSupport.loads(requestBody) flatMap {
          case y: YamlObject => YamlSupport.fromAST[T](y.mergeAfter(merge))(yamlFormat.asInstanceOf[YamlReader[T]])
          case y: YamlValue =>
            Failure(InvalidDataException(s"The value $y does not seem to be a complete yaml object."))
        }

      case Some("application/json") =>
        JsonSupport.loads(requestBody) flatMap {
          case j: JObject =>
            val mapJson = JsonSupport.toAST[Map[String, Any]](merge)
            JsonSupport.fromAST[T](j merge mapJson)

          case j: JValue => Failure(InvalidDataException(s"The value $j  does not seem to be a complete json object."))
        }
      case Some(other) => Failure(InvalidDataException(s"Don't understand content-type $other"))

      case None => Failure(InvalidDataException(s"Requires Content-Type header"))
    }
  }

}
