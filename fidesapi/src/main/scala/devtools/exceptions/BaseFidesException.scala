package devtools.exceptions

import com.typesafe.scalalogging.LazyLogging

/** Base class of any custom exceptions thrown by fides. All custom exceptions expect a list of possible errors */
abstract class BaseFidesException(val name: String, val errors: Seq[String])
  extends Exception(s"$name:${errors.mkString(",")}") with LazyLogging {
  logger.warn(getMessage)

}
