package devtools.util
import pdi.jwt.algorithms.JwtHmacAlgorithm
import pdi.jwt.{Jwt, JwtAlgorithm}

import scala.util.Random

object JwtUtil {

  private val random = Random

  def algorithm: JwtHmacAlgorithm = JwtAlgorithm.HS256
  def generateToken(): String     = random.alphanumeric.take(40).mkString

  /** Return the claim portion of this JWT as a map if it is properly encoded. */
  def decodeClaim(token: String, key: String): Option[Map[String, String]] =
    Jwt
      .decodeRaw(token, key, Seq(algorithm))
      .flatMap(JsonSupport.parseToObj[Map[String, String]])
      .toOption

  def encode(claim: Map[String, Any], key: String): String = Jwt.encode(JsonSupport.dumps(claim), key, algorithm)
}
