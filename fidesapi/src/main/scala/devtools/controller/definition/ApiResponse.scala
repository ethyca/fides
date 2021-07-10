package devtools.controller.definition

import com.typesafe.scalalogging.LazyLogging
import devtools.exceptions.BaseFidesException
import org.json4s.Formats
import org.scalatra._

import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success, Try}
final case class ApiResponse[T](errors: Seq[String] = Seq(), data: Option[T] = None)

/** Uniform response structure */
object ApiResponse extends LazyLogging {

  def success(t: Any): ActionResult = Ok(ApiResponse(data = Some(t)))

  def failure(e: Throwable): ActionResult = BadRequest(ApiResponse(errors = errorsFromThrowable(e), data = Some(Seq())))

  def failure(msg: String): ActionResult = BadRequest(ApiResponse(errors = Seq(msg), data = Some(Seq())))

  def fromTry[T](f: Try[T]): ActionResult =
    f match {
      case Success(t) => Ok(ApiResponse[T](data = Some(t)))
      case Failure(e) => failure(e)
    }

  def fromOption[T](o: Option[T]): ActionResult =
    o match {
      case Some(_) => Ok(ApiResponse[T](data = o))
      case None    => NotFound(ApiResponse[T](errors = Seq("not found")))
    }

  def errorsFromThrowable(t: Throwable): Seq[String] =
    t match {
      case e: BaseFidesException => e.errors
      case e: Throwable          => Seq(e.getMessage)
    }

  /** Handle async response with option None => NotFound. */
  def asyncResponse[ResponseType](
    f: => Future[ResponseType]
  )(implicit executor: ExecutionContext, context: ScalatraContext, formats: Formats): AsyncResult =
    new AsyncResult {
      val is: Future[ActionResult] = withLogging(
        request.getRequestURI,
        request.getIntHeader("user-id"),
        f map { t => fromTry(Try(t)) } recoverWith { case e: Throwable => Future(failure(e)) }
      )
    }

  /** Handle async response with option None => NotFound. */
  def asyncOptionResponse[ResponseType](
    f: => Future[Option[ResponseType]]
  )(implicit executor: ExecutionContext, context: ScalatraContext, formats: Formats): AsyncResult = {

    new AsyncResult {
      val is: Future[ActionResult] = withLogging(
        request.getRequestURI,
        request.getIntHeader("user-id"),
        (f map fromOption).recoverWith { case e: Throwable => Future(failure(e)) }
      )

    }
  }

  /** Uniform output logging */
  def withLogging(uri: String, user: Long, fr: Future[ActionResult])(implicit
    executor: ExecutionContext
  ): Future[ActionResult] = {
    fr.onComplete {
      case Success(result)    => logger.info("{}:{}:{}", uri, user, result.status)
      case Failure(exception) => logger.info("{}:{}:{}", uri, user, exception)
    }
    fr
  }
}

final case class ErrorResponse(errors: Seq[String])

object ErrorResponse extends LazyLogging {
  def apply(e: Throwable): ErrorResponse = {
    logger.error(e.getMessage)
    e match {
      case b: BaseFidesException => ErrorResponse(b.errors)
      case _: Throwable          => ErrorResponse(List(e.getMessage))
    }
  }
}
