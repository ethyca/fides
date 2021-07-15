package devtools.controller.definition

import devtools.controller.RequestContext
import devtools.persist.dao.UserDAO
import devtools.util.waitFor
import org.scalatra.ScalatraBase

import scala.util.{Failure, Success, Try}

/** A Placeholder implementation for authentication. Currently this implementation _only_
  * requires that a user-id is provided in the header and that this id corresponds
  * to an actual existing user id.
  *
  * This is a temporary implementation to support user management development on the CLI.
  * We will probably need something a bit more ... robust.
  */
trait AuthenticationSupport extends ScalatraBase {

  /** Temporary "declare that I am user X" placeholder authentication */
  val UserIdHeader = "user-id"
  val userDAO: UserDAO

  /** Pass through container for storing information captured from the request that will
    * need to be passed through the api.
    */
  val requestContext: RequestContext = new RequestContext()

  /** A simple interceptor that checks for the existence
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
              case None       => halt(status = 401, headers = Map("WWW-Authenticate" -> "user-id"))
              case Some(user) => requestContext.user = user; requestContext.organizationId = user.organizationId
            }
        }
    }
  }
}
