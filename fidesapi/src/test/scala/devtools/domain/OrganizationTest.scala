package devtools.domain

import devtools.App
import devtools.Generators.OrgGen
import devtools.util.FidesYamlProtocols
import faker._
class OrganizationTest
  extends DomainObjectTestBase[Organization, Long](
    App.organizationService,
    OrgGen,
    FidesYamlProtocols.OrganizationFormat
  ) {

  override def editValue(t: Organization): Organization         = t.copy(fidesKey = Name.name)
  override def maskForComparison(t: Organization): Organization = t.copy(creationTime = None, lastUpdateTime = None)
  test(s"Organization.fidesKey must be unique") {
    testInsertConstraint({ org: Organization => this.generator.sample.get.copy(fidesKey = org.fidesKey) })
  }

}
