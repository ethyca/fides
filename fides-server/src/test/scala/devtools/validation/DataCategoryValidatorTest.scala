package devtools.validation

import devtools.App
import devtools.Generators._
import devtools.domain.enums.PolicyValueGrouping
import devtools.domain.enums.RuleInclusion.ALL
import devtools.domain.policy.PolicyRule
import devtools.domain.{DataCategory, SystemObject}
import devtools.util.waitFor
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

class DataCategoryValidatorTest
  extends ValidatorTestBase[DataCategory, Long](DataCategoryGen, App.dataCategoryDAO, App.dataCategoryValidator) {

  private val sDao                   = App.systemDAO
  private val prDao                  = App.policyRuleDAO
  var newKey: String                 = ""
  var newId: Long                    = _
  var newTaxonomyValue: DataCategory = _
  var newSystem: SystemObject        = _
  var newPolicyRule: PolicyRule      = _
  var child: DataCategory            = _
  override def beforeAll(): Unit = {
    newKey = fidesKey
    newTaxonomyValue = waitFor(dao.create(DataCategory(0, None, 1, newKey, None, None, None)))
    newId = newTaxonomyValue.id
    newSystem = waitFor(
      sDao.create(
        blankSystem.copy(privacyDeclarations = Seq(DeclarationGen.sample.get.copy(dataCategories = Set(newKey))))
      )
    )

    newPolicyRule = waitFor(
      prDao.create(
        PolicyRuleGen.sample.get.copy(organizationId = 1, dataCategories = PolicyValueGrouping(ALL, Set(newKey)))
      )
    )
    createdIds.add(newId)
    child = waitFor(dao.create(DataCategory(0, Some(newId), 1, newKey + "child", None, None, None)))
    createdIds.add(child.id)
  }

  override def afterAll(): Unit = {
    super.afterAll()
    sDao.delete(newSystem.id)
  }

  test("create requires organization exists") {
    createValidationErrors(_.copy(organizationId = randomLong)) should containMatchString("organization")
  }

  test("create requires parent exists ") {
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
      DataCategory(newId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) should containMatchString("is in use in systems")
    //attempt to delete with the new key
    deleteValidationErrors(newId) should containMatchString("is in use in systems")

    // test in policy rules
    updateValidationErrors(
      DataCategory(newId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) should containMatchString("is in use in policy rules")
    //attempt to delete with the new key
    deleteValidationErrors(newId) should containMatchString("is in use in policy rules")

    //delete system, update and delete should pass
    waitFor(sDao.delete(newSystem.id))
    updateValidationErrors(
      DataCategory(newId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) shouldNot containMatchString("systems")

    deleteValidationErrors(newId) shouldNot containMatchString("systems")

    //delete policyRule, update and delete should pass
    waitFor(prDao.delete(newPolicyRule.id))
    updateValidationErrors(
      DataCategory(newId, None, 1, "tryingToChangeTheFidesKeyOfAnInUseValue", None, None, None),
      newTaxonomyValue
    ) shouldNot containMatchString("is in use in policy rules")
    //attempt to delete with the new key
    deleteValidationErrors(newId) shouldNot containMatchString("is in use in policy rules")
  }

  test("delete with children") {
    deleteValidationErrors(newId) should containMatchString("child")
  }
}
