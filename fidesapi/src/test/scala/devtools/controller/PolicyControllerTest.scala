package devtools.controller

import devtools.App
import devtools.Generators.PolicyGen
import devtools.domain.policy.Policy

class PolicyControllerTest extends ControllerTestBase[Policy, Long]("policy", PolicyGen, App.policyController) {
  override def editValue(t: Policy): Policy = generator.sample.get.copy(id = t.id)

  override def isValid(t: Policy): Boolean = t.id > 0 && t.fidesKey.nonEmpty

  override def withoutMergeValues(t: Policy): Map[String, Any] =
    super.withoutMergeValues(t.copy(rules = None, versionStamp = None))

}
