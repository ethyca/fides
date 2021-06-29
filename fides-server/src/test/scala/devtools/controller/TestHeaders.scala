package devtools.controller

import devtools.App
import devtools.util.{JwtUtil, waitFor}

trait TestHeaders {

  val token: String = {
    val apiKey = waitFor(App.userDAO.findById(1)).get.apiKey
    JwtUtil.encode(Map("uid" -> 1), apiKey)
  }
  val testHeaders = Seq("user-id" -> "1", "Authorization" -> s"Bearer $token")

  def withTestHeaders(t: (String, String)): Seq[(String, String)] = testHeaders :+ t
}
