package devtools.util

import scala.util.matching.Regex

object Sanitization {

  /** reject anything that's not alphanumeric, _, or - */
  val uniqueKeySanitizerPattern: Regex            = "[^a-zA-Z_0-9-]".r

  /** Sanitize unique identifiers, which need to work as url parameter values. */
  def sanitizeUniqueIdentifier(s: String): String = uniqueKeySanitizerPattern.replaceAllIn(s, "_")
}
