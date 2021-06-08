package devtools.controller

import devtools.domain.User

/** Storage for request-scoped data, e.g request user, organization, etc. */
class RequestContext {

  var user: User                   = _
  var organizationId: Option[Long] = None
  var versionStamp: Option[Long]   = None
}

object RequestContext {
  def apply(user: User): RequestContext = {
    val v: RequestContext = new RequestContext
    v.user = user
    v.organizationId = Some(user.organizationId)
    v
  }

}
