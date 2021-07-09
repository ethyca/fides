package devtools

import com.typesafe.scalalogging.LazyLogging

import scala.concurrent.duration.Duration
import scala.concurrent.{Await, Future}

package object util extends LazyLogging {

  def fatal(msg: String): Unit = {
    logger.error(s"Fatal error: $msg")
    System.exit(1)
  }

  def waitFor[U](f: => Future[U]): U = { Await.result(f, Duration.Inf) }

  /** Group a sequence of tuples into nested maps.
    * terminalF processes the lowest level of product type.
    */

  def mapGrouping(ts: Seq[Product], terminalF: Product => Any, indexes: Seq[Int]): AnyRef = {
    indexes match {
      case Seq() => ts.map(terminalF)
      case Seq(head, tail @ _*) => {
        val x: Map[Any, Seq[Product]] = ts.groupBy(_.productElement(head))
        x.map(inner => inner._1 -> mapGrouping(inner._2, terminalF, tail))
      }
    }

  }
}
