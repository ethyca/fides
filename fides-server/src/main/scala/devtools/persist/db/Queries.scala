package devtools.persist.db

import devtools.persist.db.Tables._
import slick.lifted.TableQuery
object Queries {
  lazy val organizationQuery       = TableQuery[OrganizationQuery]
  lazy val systemQuery             = TableQuery[SystemQuery]
  lazy val privacyDeclarationQuery = TableQuery[PrivacyDeclarationQuery]
  lazy val registryQuery           = TableQuery[RegistryQuery]
  lazy val dataCategoryQuery       = TableQuery[DataCategoryQuery]
  lazy val dataUseQuery            = TableQuery[DataUseQuery]
  lazy val dataQualifierQuery      = TableQuery[DataQualifierQuery]
  lazy val dataSubjectQuery        = TableQuery[DataSubjectQuery]
  lazy val policyQuery             = TableQuery[PolicyQuery]
  lazy val policyRuleQuery         = TableQuery[PolicyRuleQuery]
  lazy val userQuery               = TableQuery[UserQuery]
  lazy val approvalQuery           = TableQuery[ApprovalQuery]
  lazy val auditLogQuery           = TableQuery[AuditLogQuery]
  lazy val datasetQuery            = TableQuery[DatasetQuery]
  lazy val datasetFieldQuery       = TableQuery[DatasetFieldQuery]
}
