package devtools.util

import configs.ConfigReader
import devtools.util.ConfigLoader.{optionalProperty, requiredProperty}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.reflect.ManifestFactory

class ConfigLoaderTest extends AnyFunSuite {

  test(testName = "config default values are properly loaded") {

    val v = requiredProperty("fides.db.driver")(ConfigReader[String], ManifestFactory.classType(classOf[String]))
    optionalProperty("fides.db.driver")(ConfigReader[String], ManifestFactory.classType(classOf[String])) shouldBe Some(
      v
    )
    optionalProperty("I don't exist")(ConfigReader[String], ManifestFactory.classType(classOf[String])) shouldBe None
  }

}
