package devtools.domain.policy

import devtools.App
import devtools.Generators.PolicyGen
import devtools.domain.DomainObjectTestBase
import devtools.util.FidesYamlProtocols
import faker.Name
class PolicyTest
  extends DomainObjectTestBase[Policy, Long](App.policyService, PolicyGen, FidesYamlProtocols.PolicyFormat) {

  override def editValue(t: Policy): Policy = t.copy(name = Some(Name.name))
  override def maskForComparison(t: Policy): Policy =
    t.copy(lastUpdateTime = None, creationTime = None, rules = None)
}
