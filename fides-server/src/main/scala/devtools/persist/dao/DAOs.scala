package devtools.persist.dao

/** Collection of DAOS to avoid passing them around one at a time */
class DAOs(
  val approvalDAO: ApprovalDAO,
  val auditLogDAO: AuditLogDAO,
  val dataCategoryDAO: DataCategoryDAO,
  val dataQualifierDAO: DataQualifierDAO,
  val dataUseDAO: DataUseDAO,
  val organizationDAO: OrganizationDAO,
  val policyDAO: PolicyDAO,
  val policyRuleDAO: PolicyRuleDAO,
  val registryDAO: RegistryDAO,
  val systemDAO: SystemDAO,
  val dataSubjectCategoryDAO: DataSubjectCategoryDAO,
  val userDAO: UserDAO,
  val datasetDAO: DatasetDAO,
  val datasetTableDAO: DatasetTableDAO,
  val datasetFieldDAO: DatasetFieldDAO
) {}
