package devtools.domain

import devtools.App
import devtools.Generators.{ApprovalGen, versionStamp}
import devtools.util.FidesYamlProtocols

class ApprovalTest
  extends DomainObjectTestBase[Approval, Long](App.approvalService, ApprovalGen, FidesYamlProtocols.ApprovalFormat) {

  override def editValue(t: Approval): Approval = t.copy(versionStamp = versionStamp)

  override def maskForComparison(t: Approval): Approval = t.copy(creationTime = None)
}
