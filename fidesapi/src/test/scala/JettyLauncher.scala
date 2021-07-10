import devtools.util.ConfigLoader.optionalProperty
import org.eclipse.jetty.server.Server
import org.eclipse.jetty.servlet.DefaultServlet
import org.eclipse.jetty.webapp.WebAppContext
import org.scalatra.servlet.ScalatraListener

object JettyLauncher {

  def main(args: Array[String]): Unit = {
    val port    = optionalProperty[Int]("fides.port").getOrElse(8080)
    val server  = new Server(port)
    val context = new WebAppContext()
    context setContextPath "/"
    context.setResourceBase("src/main/webapp")
    context.setInitParameter("org.scalatra.cors.allowedOrigins", "*")
    context.setInitParameter("org.scalatra.cors.allowCredentials", "false")
    //    context.setInitParameter(ScalatraListener.LifeCycleKey, "org.yourdomain.project.ScalatraBootstrap")
    context.addEventListener(new ScalatraListener)
    context.addServlet(classOf[DefaultServlet], "/")
    server.setHandler(context)
    server.start()
    server.join()
  }
}
