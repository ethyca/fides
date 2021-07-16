package devtools.util

import scala.util.matching.Regex

object Sanitization {

  /** reject anything that's not alphanumeric, _, or - */
  val uniqueKeySanitizerPattern: Regex = "[^a-zA-Z_0-9-]".r
  val fieldSanitizerPattern: Regex     = "[^.a-zA-Z_0-9-]".r
  /** Sanitize unique identifiers, which need to work as url parameter values. */
  def sanitizeUniqueIdentifier(s: String): String = uniqueKeySanitizerPattern.replaceAllIn(s, "_")

  /** Dataset references can include '.' characters to separate fields, but each section must be nonEmpty. */
  def isValidDatasetReference(s: String): Boolean = {
    val sections = s.split('.')
    if (sections.length == 0) false else sections.forall(s => s.nonEmpty && isValidFidesKey(s))
  }

  def isValidDatasetFieldReference(s: String): Boolean = fieldSanitizerPattern.replaceAllIn(s, "_") == s

  def isValidFidesKey(s: String): Boolean = s == sanitizeUniqueIdentifier(s)

}
