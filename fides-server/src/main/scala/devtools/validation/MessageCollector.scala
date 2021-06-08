package devtools.validation

import devtools.exceptions.ValidationException

import scala.collection.mutable.{Map => MMap, Set => MSet}
import scala.concurrent.Future

/** collect messages, with special handling for errors */
class MessageCollector(val warnings: MSet[String] = MSet(), val errors: MSet[String] = MSet()) {

  def addError(value: String): Unit = errors.add(value)

  def addWarning(value: String): Unit = warnings.add(value)

  def hasErrors: Boolean = errors.nonEmpty

  /** return a failure only if there are values stored as errors */
  def asFuture(): Future[Unit] =
    errors.size match {
      case 0 => Future.successful(())
      case _ => Future.failed(ValidationException(errors.toList))
    }

  override def toString = s"MessageCollector($toMap)"

  def toMap: Map[String, Set[String]] = Map("errors" -> errors.toSet, "warnings" -> warnings.toSet)

}
