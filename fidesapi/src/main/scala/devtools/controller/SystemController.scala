package devtools.controller

import devtools.controller.definition.ApiResponse.{asyncOptionResponse, asyncResponse}
import devtools.controller.definition.{BaseController, GetByUniqueKey, LongPK}
import devtools.domain.{Approval, SystemObject}
import devtools.exceptions.NoSuchValueException
import devtools.persist.dao.{DAOs, UserDAO}
import devtools.persist.service.{ApprovalService, PolicyService, SystemService}
import devtools.rating.Evaluator
import devtools.util.FidesYamlProtocols
import net.jcazevedo.moultingyaml.YamlFormat
import org.scalatra.swagger.Swagger

import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success}

class SystemController(
  val service: SystemService,
  val policyService: PolicyService,
  val approvalService: ApprovalService,
  val daos: DAOs,
  val swagger: Swagger
)(implicit
  executor: ExecutionContext
) extends BaseController[SystemObject, Long] with LongPK[SystemObject] with GetByUniqueKey[SystemObject] {

  val yamlFormat: YamlFormat[SystemObject] = FidesYamlProtocols.SystemObjectFormat
  val userDAO: UserDAO                     = daos.userDAO
  val evaluator: Evaluator                 = new Evaluator(daos)
  /** Default input values that are part of system object but we don't expect as part of the post */

  override val inputMergeMap = Map("id" -> 0, "creationTime" -> null, "lastUpdateTime" -> null)

  post(
    "/validateForCreate",
    operation(
      apiOperation[SystemObject](s"validateForCreate system")
        .summary(s"validateForCreate (pre-flight) a system and report on any errors")
    )
  ) {
    asyncResponse {
      ingest(request.body, Option(request.getHeader("Content-Type")), inputMergeMap) match {
        case Success(t)         => service.validator.validateForCreate(t, requestContext).map(_ => t)
        case Failure(exception) => Future.failed(exception)
      }
    }
  }

  /* Evaluate endpoints */
  get(
    "/evaluate/:fidesKey",
    operation(
      apiOperation[Approval](s"evaluate a single system and return the approval value")
        .summary("run and store evaluation on the specified system.")
        .parameters(
          queryParam[String]("tag").description(s"optional commit tag"),
          queryParam[String]("message").description(s"optional commit message")
        )
    )
  ) {

    val fidesKey = params("fidesKey")
    val tag      = params.get("tag")
    val message  = params.get("message")

    asyncResponse {
      service.findByUniqueKey(requestContext.organizationId, fidesKey).flatMap {
        case Some(s) => evaluator.systemEvaluate(s, requestContext.user.id, tag, message)
        case None    => Future.failed(NoSuchValueException("fides-key", fidesKey))
      }
    }
  }

  get(
    "/evaluate/:fidesKey/last",
    operation(
      apiOperation[Approval](s"Current state of the system approval, if it exists")
        .summary("Return the current approval state of the specified system.")
    )
  ) {
    asyncOptionResponse {
      service.findByUniqueKey(requestContext.organizationId, params("fidesKey")).flatMap {
        case Some(s) => approvalService.mostRecentSystem(s.id)
        case None    => Future.failed(NoSuchValueException("fides-key", params("fidesKey")))
      }
    }
  }

  post(
    "/evaluate/dry-run",
    operation(
      apiOperation[Approval](s"evaluate a the posted system and return the approval value")
        .summary("Evaluate the posted system as a 'dry-run' only.")
    )
  ) {

    asyncResponse {
      ingest(request.body, Option(request.getHeader("Content-Type")), inputMergeMap) match {
        case Success(t)         => evaluator.systemDryRun(t, requestContext.user.id)
        case Failure(exception) => Future.failed(exception)
      }
    }
  }

}
