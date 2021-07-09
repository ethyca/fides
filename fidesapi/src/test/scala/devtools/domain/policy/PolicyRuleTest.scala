package devtools.domain.policy

import devtools.Generators.PolicyRuleGen
import devtools.domain.DomainObjectTestBase
import devtools.util.FidesYamlProtocols
import devtools.{App, TestUtils}
import faker.Name
import org.scalatest.BeforeAndAfterAll

class PolicyRuleTest
  extends DomainObjectTestBase[PolicyRule, Long](
    App.policyRuleService,
    PolicyRuleGen,
    FidesYamlProtocols.PolicyRuleFormat
  ) with TestUtils with BeforeAndAfterAll {
  override def editValue(t: PolicyRule): PolicyRule         = t.copy(name = Some(Name.name))
  override def maskForComparison(t: PolicyRule): PolicyRule = t.copy(lastUpdateTime = None, creationTime = None)

}
