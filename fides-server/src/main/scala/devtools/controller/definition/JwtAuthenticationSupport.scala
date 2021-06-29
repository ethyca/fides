package devtools.controller.definition

import com.typesafe.scalalogging.LazyLogging
import devtools.controller.RequestContext
import devtools.domain.User
import devtools.persist.dao.UserDAO
import devtools.util.{JwtUtil, waitFor}
import org.scalatra.ScalatraBase

import javax.servlet.http.HttpServletRequest
import scala.util.{Failure, Success, Try}

/** A Placeholder implementation for authentication. Currently this implementation _only_
  * requires that a user-id is provided in the header and that this id corresponds
  * to an actual existing user id.
  *
  * This is a temporary implementation to support user management development on the CLI.
  * We will probably need something a bit more ... robust.
  */
trait JwtAuthenticationSupport extends ScalatraBase with LazyLogging {

  /** Temporary "declare that I am user X" placeholder authentication */
  val UserIdHeader = "user-id"
  val userDAO: UserDAO

  /** Pass through container for storing information captured from the request that will
    * need to be passed through the api.
    */
  val requestContext: RequestContext = new RequestContext()

  /**
    * A simple interceptor that checks for the existence
    * of userId
    */
  before() {
    // we check the host where the request is made
    val userId: Option[String] = Option(request.getHeader(UserIdHeader))

    userId match {
      case None => halt(status = 401, body = "No user id set", headers = Map("WWW-Authenticate" -> "user-id"))
      case Some(idString) =>
        Try(idString.toInt) match {
          case Failure(_) =>
            halt(
              status = 401,
              body = "User id requires an integer value",
              headers = Map("WWW-Authenticate" -> "user-id")
            )
          case Success(id) =>
            waitFor(userDAO.findById(id)) match {
              case None => halt(status = 401, headers = Map("WWW-Authenticate" -> "user-id"))
              case Some(user) =>
                validateToken(request, user)
                requestContext.user = user
                requestContext.organizationId = user.organizationId
            }
        }
    }
  }

  // -------------------------------------------------
  // token handling
  // -------------------------------------------------
  private val headerTokenRegex = """Bearer (.+?)""".r

  def extractToken(request: HttpServletRequest): Option[String] =
    Option(request.getHeader("Authorization")) collect {
      case headerTokenRegex(token) => token
    }

  def validateToken(request: HttpServletRequest, user: User): Unit =
    extractToken(request).flatMap(JwtUtil.decodeClaim(_, user.apiKey)) match {
      case Some(m) if m("uid") == user.id.toString => ()
      case _                                       => {
        logger.info(s"401: ${request.getRequestURI}")
        halt(status = 401, headers = Map("WWW-Authenticate" -> "Invalid token"))
      }
    }

}
