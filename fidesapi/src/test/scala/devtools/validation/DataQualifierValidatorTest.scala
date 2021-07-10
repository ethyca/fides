package devtools.validation

import devtools.App
import devtools.Generators._
import devtools.domain.policy.PolicyRule
import devtools.domain.{DataQualifier, SystemObject}
import devtools.util.waitFor
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DataQualifierValidatorTest
  extends ValidatorTestBase[DataQualifier, Long](DataQualifierGen, App.dataQualifierDAO, App.dataQualifierValidator) {

  private val systemService           = App.systemService
  private val prDao                   = App.policyRuleDAO
  var newKey: String                  = ""
  var newKeyId: Long                  = 0
  var newTaxonomyValue: DataQualifier = _
  var newSystem: SystemObject         = _
  var newPolicyRule: PolicyRule       = _
  var child: DataQualifier            = _
  override def beforeAll(): Unit = {
    newKey = fidesKey
    newTaxonomyValue = waitFor(dao.create(DataQualifier(0, None, 1, newKey, None, None, None)))
    Thread.sleep(100)
    newKeyId = newTaxonomyValue.id
    newSystem = waitFor(
      systemService.create(
        blankSystem.copy(privacyDeclarations = Some(Seq(DeclarationGen.sample.get.copy(dataQualifier = newKey)))),
        requestContext
      )
    )
    newPolicyRule = waitFor(
      prDao.create(PolicyRuleGen.sample.get.copy(organizationId = 1, dataQualifier = Some(newKey)))
    )

    createdIds.add(newKeyId)
    child = waitFor(dao.create(DataQualifier(0, Some(newKeyId), 1, newKey + "child", None, None, None)))
    createdIds.add(child.id)
  }

  override def afterAll(): Unit = {
    super.afterAll()
    systemService.dao.delete(newSystem.id)
  }

  test("create requires organization exists") {
    createValidationErrors(_.copy(organizationId = randomLong)) should containMatchString("organization")
  }

  test("create requires parent exists") {
    createValidationErrors(_.copy(parentId = Some(randomLong))) should containMatchString("parent")
  }

  test("update requires parent exists if not null") {
    updateValidationErrors(
      gen.sample.get.copy(parentId = None),
      _.copy(parentId = Some(randomLong))
    ) should containMatchString("parentId")
  }

  test("update or delete with fides key in use by system fails") {
    //attempt to update with new key
    updateValidationErrors(
      DataQualifier(newKeyId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) should containMatchString("is in use in systems")
    //attempt to delete with the new key
    deleteValidationErrors(newKeyId) should containMatchString("is in use in systems")

    // test in policy rules
    updateValidationErrors(
      DataQualifier(newKeyId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) should containMatchString("is in use in policy rules")
    //attempt to delete with the new key
    deleteValidationErrors(newKeyId) should containMatchString("is in use in policy rules")

    //delete system, update and delete should pass
    waitFor(systemService.dao.delete(newSystem.id))
    updateValidationErrors(
      DataQualifier(newKeyId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) shouldNot containMatchString("systems")

    deleteValidationErrors(newKeyId) shouldNot containMatchString("systems")

    //delete policyRule, update and delete should pass
    waitFor(prDao.delete(newPolicyRule.id))
    updateValidationErrors(
      DataQualifier(newKeyId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) shouldNot containMatchString("is in use in policy rules")
    //attempt to delete with the new key
    deleteValidationErrors(newKeyId) shouldNot containMatchString("is in use in policy rules")
  }

  test("delete with children") {
    deleteValidationErrors(newKeyId) should containMatchString("child")
  }
}
