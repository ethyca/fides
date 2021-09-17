package devtools.persist.db

import com.mchange.v2.c3p0.ComboPooledDataSource
import devtools.util.ConfigLoader.{optionally, requiredProperty}
import org.slf4j.{Logger, LoggerFactory}
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.duration.DurationInt

object DB {
  val logger: Logger = LoggerFactory.getLogger(getClass)

  private lazy val ds: ComboPooledDataSource = {
    val ds = new ComboPooledDataSource

    ds.setDriverClass(requiredProperty[String]("fides.db.driver"))
    ds.setJdbcUrl(requiredProperty[String]("fides.db.jdbc.url"))
    ds.setUser(requiredProperty[String]("fides.db.jdbc.user"))
    ds.setPassword(requiredProperty[String]("fides.db.jdbc.password"))
    ds.setAutoCommitOnClose(true)
    //optional settings
    optionally[Int]("fides.db.jdbc.minPoolSize", i => ds.setMinPoolSize(i))
    optionally[Int]("fides.db.jdbc.maxPoolSize", i => ds.setMaxPoolSize(i))
    optionally[Int]("fides.db.jdbc.maxStatements", i => ds.setMaxStatements(i))
    optionally[Int]("fides.db.jdbc.acquireIncrement", i => ds.setAcquireIncrement(i))

    ds
  }
  /*  Mostly set to default values.  */
  val dbExecutor: AsyncExecutor = AsyncExecutor(
    "db-async-executor",
    minThreads = 20,
    maxThreads = 20,
    queueSize = 1000,
    maxConnections = 20,
    keepAliveTime = 1.minute,
    registerMbeans = false
  )

  lazy val db: Database =
    Database.forDataSource(ds, maxConnections = None, executor = dbExecutor, keepAliveConnection = false)

  logger.info("Created c3p0 connection pool")

  def stop(): Unit = {
    logger.info("Closing c3po connection pool")
    db.close()
  }

}
