package devtools.controller

trait TestHeaders {

  val testHeaders = Seq("user-id" -> "1")

  def withTestHeaders(t: (String, String)): Seq[(String, String)] = testHeaders :+ t
}
