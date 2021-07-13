package devtools.util

import devtools.TestUtils
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class JwtUtilTest extends AnyFunSuite {

  test(testName = "testEncodeDecode") {
    val secret =  JwtUtil.generateToken()
    val token   = JwtUtil.encode(Map("uid" -> 1), secret)
    val decoded = JwtUtil.decodeClaim(token, secret)
    decoded shouldBe Some(Map("uid" -> "1"))
  }




}
