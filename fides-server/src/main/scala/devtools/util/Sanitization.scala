package devtools.util

import scala.util.matching.Regex

object Sanitization {

  /** reject anything that's not alphanumeric, _, or - */
  val uniqueKeySanitizerPattern: Regex            = "[^a-zA-Z_0-9-]".r
  def sanitizeUniqueIdentifier(s: String): String = uniqueKeySanitizerPattern.replaceAllIn(s, "_")
}
