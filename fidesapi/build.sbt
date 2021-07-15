import java.io.{File, FileInputStream}
import java.util.Properties

conflictManager := ConflictManager.latestRevision
val ScalatraVersion = "2.7.1"
enablePlugins(CodegenPlugin)
enablePlugins(FlywayPlugin)
enablePlugins(ScalatraPlugin)
ThisBuild / scalaVersion := "2.12.8"
ThisBuild / organization := "ethyca"

fork := true

//require java11
initialize := {
  val _ = initialize.value // Needed to run previous initialization.
  assert(scala.util.Properties.isJavaAtLeast("11"), "This project requires Java 11 or later")
}


val properties = {
  val p = new Properties()
  p.load(new FileInputStream(new File("src/main/resources/reference.conf")))
  try {
    p.load(new FileInputStream(new File("src/main/resources/application.conf")))
  } catch {
    case _: Exception => ()
  }

  //overwrite any values with env values, if they have been set.
  //env values are name translated, from e.g. a.b.c.d -> A_B_C_D
  p.keySet().forEach { k =>
    {
      val envKey = k.toString.replace('.', '_').toUpperCase
      sys.env.get(envKey).foreach(p.put(k, _))
    }
  }
  p
}

lazy val root = (project in file("."))
  .settings(
    name := "fidesapi",
    version := "0.1.0-SNAPSHOT",
    libraryDependencies ++= Seq(
      "org.scalatra" %% "scalatra" % ScalatraVersion,
      //logging
      "com.typesafe.scala-logging" %% "scala-logging"     % "3.9.4",
      "ch.qos.logback"              % "logback-classic"   % "1.2.3"            % "runtime",
      "org.eclipse.jetty"           % "jetty-webapp"      % "9.4.36.v20210114" % "container",
      "javax.servlet"               % "javax.servlet-api" % "4.0.1"            % "provided",
      //json support
      "org.scalatra" %% "scalatra-json"  % "2.7.1",
      "org.json4s"   %% "json4s-jackson" % "3.6.11",
      "org.json4s"   %% "json4s-core"    % "3.6.11",
      "org.json4s"   %% "json4s-native"  % "3.6.11",
      //http
      "org.scalaj" %% "scalaj-http" % "2.4.2",
      //yaml,
      "net.jcazevedo" %% "moultingyaml" % "0.4.2",
      // config support
      "com.github.kxbmap" % "configs_2.12" % "0.6.1",
      //swagger support
      "org.scalatra" %% "scalatra-swagger" % "2.7.1",
      // views
      "org.scalatra" %% "scalatra-scalate" % "2.7.1",
      // jwt
      "com.github.jwt-scala" %% "jwt-core" % "8.0.2",
      //cache
      "com.github.blemale" %% "scaffeine" % "5.0.0",
      // db support
      "c3p0"               % "c3p0"                 % "0.9.1.2",
      "mysql"              % "mysql-connector-java" % "8.0.25",
      "com.typesafe.slick" % "slick_2.12"           % "3.3.3", // excludeAll ExclusionRule("org.scala-lang.modules", "scala-collection-compat_2.12"),
      "com.typesafe.slick" % "slick-codegen_2.12"   % "3.3.3", // excludeAll ExclusionRule("org.scala-lang.modules", "scala-collection-compat_2.12"),
      //testing
      "org.scalatra"         %% "scalatra-scalatest" % ScalatraVersion % "test",
      "org.scalatest"        %% "scalatest"          % "3.2.9"         % "test",
      "org.scalactic"        %% "scalactic"          % "3.2.9",
      "com.github.pjfanning" %% "scala-faker"        % "0.5.3"         % "test",
      "org.scalacheck"       %% "scalacheck"         % "1.15.4"        % "test",
      "org.scalamock"        %% "scalamock"          % "5.1.0"         % "test"
    )
  )

Test / mainClass := Some("JettyLauncher")

//flywayResolvers
val dbConfUser = properties.getProperty("fides.db.jdbc.user")
val dbConfPass = properties.getProperty("fides.db.jdbc.password")
val dbConfUrl  = properties.getProperty("fides.db.jdbc.url").replace("\"", "")

flywayUrl := dbConfUrl
flywayUser := dbConfUser
flywayPassword := dbConfPass
flywayLocations := Seq("filesystem:db/migrations")
slickCodegenDatabaseUrl := dbConfUrl
slickCodegenDatabaseUser := dbConfUser
slickCodegenDatabasePassword := dbConfPass
slickCodegenDriver := slick.jdbc.MySQLProfile
slickCodegenJdbcDriver := "com.mysql.cj.jdbc.Driver"
slickCodegenOutputPackage := "devtools.persist.tables.generated"
slickCodegenOutputDir := file("src/main/scala")

//don't generate a slick model for the flyway migration tracking table
Compile / slickCodegenExcludedTables := Seq("flyway_schema_history")

Global / excludeLintKeys += slickCodegenExcludedTables
Global / excludeLintKeys += slickCodegenIncludedTables
//optional

scalacOptions ++= Seq("-unchecked", "-deprecation", "-feature")

wartremoverErrors ++= Seq(
  Wart.ArrayEquals,
  Wart.EitherProjectionPartial,
  Wart.Enumeration,
  Wart.ExplicitImplicitTypes,
  Wart.FinalVal,
  Wart.JavaConversions,
  Wart.Option2Iterable,
  Wart.LeakingSealed,
  Wart.ListAppend,
  Wart.FinalCaseClass
)
