package devtools.util

import com.typesafe.config.{Config, ConfigFactory}
import com.typesafe.scalalogging.LazyLogging
import configs.ConfigReader
import configs.syntax._

import scala.collection.mutable
import scala.util.{Failure, Success, Try}

/** Represents parsed config values.
  *
  *  From https://github.com/lightbend/config#standard-behavior:
  *
  * The convenience method ConfigFactory.load() loads the following (first-listed are higher priority):
  *
  * system properties
  * application.conf (all resources on classpath with this name)
  * application.json (all resources on classpath with this name)
  * application.properties (all resources on classpath with this name)
  * reference.conf (all resources on classpath with this name)
  * The idea is that libraries and frameworks should ship with a reference.conf in their jar.
  * Applications should provide an application.conf, or if they want to create multiple configurations
  * in a single JVM, they could use ConfigFactory.load("myapp") to load their own myapp.conf.
  *
  * -Dconfig.trace=loads to get output on stderr describing each file that is loaded.
  */
object ConfigLoader extends LazyLogging {

  private val config: Config = ConfigFactory.load

  private val overrideProperties: mutable.Map[String, String] = mutable.Map[String, String]()

  private def fromString[T](property: String)(implicit manifest: Manifest[T]): Try[T] =
    manifest match {

      case m if m.runtimeClass == classOf[Int]    => Try(Integer.parseInt(property)).asInstanceOf[Try[T]]
      case m if m.runtimeClass == classOf[String] => Success[String](property).asInstanceOf[Try[T]]
      case _                                      => Failure[T](new Exception(s"can't parse property type ${manifest.runtimeClass.getSimpleName}"))
    }

  /** Get from environment variable overrides to config */
  private def get[T](propertyName: String)(implicit r: ConfigReader[T], manifest: Manifest[T]): Option[T] =
    overrideProperties.get(propertyName) match {
      case None => config.get[T](propertyName).toOption
      case Some(p) =>
        fromString[T](p) match {
          case Success(t) => Some(t)
          case Failure(_) =>
            logger.warn(s"error reading ${propertyName} from env"); config.get[T](propertyName).toOption
        }
    }

  /** System will emit an info message if this property is not set and return None. */
  def optionalProperty[T](propertyName: String)(implicit r: ConfigReader[T], manifest: Manifest[T]): Option[T] = {
    val v = get[T](propertyName)
    if (v.isEmpty) { logger.info(s"optional property $propertyName was not set") }
    v
  }

  /** System will fail if this property is not specified */
  def requiredProperty[T](propertyName: String)(implicit r: ConfigReader[T], manifest: Manifest[T]): T = {
    val v = get[T](propertyName)
    if (v == None) { fatal(s"missing required property $propertyName") }
    v.get
  }

  def optionally[T](propertyName: String, setter: T => Unit)(implicit
    tag: ConfigReader[T],
    manifest: Manifest[T]
  ): Unit =
    get[T](propertyName) match {
      case Some(i) => setter(i)
      case _ =>
        logger.info(
          s"The optional property $propertyName has not been provided"
        )

    }

  def readEnv(): Unit = {
    /** i.e "a.b" => "A_B" */
    def propToEnvVarName(s: String): String = s.replace('.', '_').toUpperCase()

    val env                             = System.getenv()
    val m: mutable.TreeMap[String, Any] = mutable.TreeMap[String, Any]()
    config
      .getConfig("fides")
      .entrySet()
      .forEach(e => {
        val fkey = s"fides.${e.getKey}"
        m.put(fkey, e.getValue.unwrapped())
        val envVar = env.get(propToEnvVarName(fkey))
        if (envVar != null) {
          logger.info(s"Replacing ${fkey} with ${propToEnvVarName(fkey)} $envVar")
          overrideProperties.put(fkey, envVar)
        }
      })
  }

  def logConfig(): Unit = {

    // properties added by build process
    Seq("fides.build", "fides.version") foreach (prop => {
      optionalProperty[String](prop) match {
        case Some(v) => logger.info(s"$prop = $v")
        case _       => logger.info(s"$prop has not been set")
      }
    })

    List("fides", "java", "os").foreach { s =>
      var m: mutable.TreeMap[String, Any] = mutable.TreeMap[String, Any]()
      config.getConfig(s).entrySet().forEach(e => m += (e.getKey -> e.getValue.unwrapped()))
      for ((k, v) <- m) {
        println(s"$s.$k=$v}")
      }
    }
  }

}
