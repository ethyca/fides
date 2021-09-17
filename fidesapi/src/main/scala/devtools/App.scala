package devtools

import devtools.controller._
import devtools.persist.dao._
import devtools.persist.db.DB
import devtools.persist.service._
import devtools.rating.PolicyRuleEvaluator
import devtools.util.{Caches, ConfigLoader}
import devtools.validation._
import org.slf4j.{Logger, LoggerFactory}
import slick.jdbc.PostgresProfile

import scala.concurrent.ExecutionContextExecutor

/** App dependency management. */
@SuppressWarnings(Array("org.wartremover.warts.PublicInference"))
object App {
  val logger: Logger = LoggerFactory.getLogger(getClass)
  //config
  ConfigLoader.readEnv()
  //ConfigLoader.logConfig()
  //swagger
  implicit val swagger: DevToolsSwagger = new DevToolsSwagger
  val swaggerServlet: SwaggerServlet    = new SwaggerServlet
  //context
  implicit val executionContext: ExecutionContextExecutor = scala.concurrent.ExecutionContext.global
  //database
  val database: PostgresProfile.api.Database = DB.db

  //service
  val approvalDAO           = new ApprovalDAO(database)
  val auditLogDAO           = new AuditLogDAO(database)
  val organizationDAO       = new OrganizationDAO(database)
  val privacyDeclarationDAO = new PrivacyDeclarationDAO(database)
  val systemDAO             = new SystemDAO(database)
  val policyDAO             = new PolicyDAO(database)
  val policyRuleDAO         = new PolicyRuleDAO(database)
  val dataCategoryDAO       = new DataCategoryDAO(database)
  val dataQualifierDAO      = new DataQualifierDAO(database)
  val dataSubjectDAO        = new DataSubjectDAO(database)
  val dataUseDAO            = new DataUseDAO(database)
  val registryDAO           = new RegistryDAO(database)
  val userDAO               = new UserDAO(database)
  val datasetDAO            = new DatasetDAO(database)
  val datasetFieldDAO       = new DatasetFieldDAO(database)
  /** Convenience grouping of all DAOs. */
  val daos = new DAOs(
    approvalDAO,
    auditLogDAO,
    dataCategoryDAO,
    dataQualifierDAO,
    dataUseDAO,
    organizationDAO,
    policyDAO,
    policyRuleDAO,
    registryDAO,
    privacyDeclarationDAO,
    systemDAO,
    dataSubjectDAO,
    userDAO,
    datasetDAO,
    datasetFieldDAO
  )
  /** Convenience grouping of all caches. */
  val caches = new Caches(dataSubjectDAO, dataCategoryDAO, dataUseDAO, dataQualifierDAO)

  //validators
  val datasetFieldValidator  = new DatasetFieldValidator(daos)
  val datasetValidator       = new DatasetValidator(daos)
  val systemValidator        = new SystemValidator(daos)
  val policyValidator        = new PolicyValidator(daos)
  val registryValidator      = new RegistryValidator(daos)
  val policyRuleValidator    = new PolicyRuleValidator(daos)
  val dataUseValidator       = new DataUseValidator(daos)
  val dataQualifierValidator = new DataQualifierValidator(daos)
  val dataCategoryValidator  = new DataCategoryValidator(daos)
  val dataSubjectValidator   = new DataSubjectValidator(daos)
  val policyRuleEvaluator    = new PolicyRuleEvaluator(daos)
  //service
  val approvalService     = new ApprovalService(approvalDAO)
  val auditLogService     = new AuditLogService(auditLogDAO)
  val organizationService = new OrganizationService(organizationDAO)
  val policyRuleService   = new PolicyRuleService(policyRuleDAO)
  val datasetFieldService = new DatasetFieldService(datasetFieldDAO, datasetFieldValidator)
  val datasetService      = new DatasetService(daos, datasetFieldService, datasetValidator)
  val dataUseService      = new DataUseService(dataUseDAO, auditLogDAO, organizationDAO, dataUseValidator)
  val dataCategoryService =
    new DataCategoryService(dataCategoryDAO, auditLogDAO, organizationDAO, dataCategoryValidator)
  val dataSubjectService =
    new DataSubjectService(dataSubjectDAO, auditLogDAO, organizationDAO, dataSubjectValidator)
  val dataQualifierService =
    new DataQualifierService(dataQualifierDAO, auditLogDAO, organizationDAO, dataQualifierValidator)

  val policyService             = new PolicyService(daos, policyRuleService, policyValidator)
  val privacyDeclarationService = new PrivacyDeclarationService(daos)
  val systemService             = new SystemService(daos, privacyDeclarationService, systemValidator)(executionContext)

  val registryService = new RegistryService(daos, registryValidator)(executionContext)
  val userService     = new UserService(userDAO)
  val reportService   = new ReportService(approvalDAO)(executionContext)
  //controllers
  val approvalController      = new ApprovalController(approvalService, userDAO, swagger)
  val auditLogController      = new AuditLogController(auditLogService, userDAO, swagger)
  val organizationController  = new OrganizationController(organizationService, userDAO, swagger)
  val systemController        = new SystemController(systemService, policyService, approvalService, daos, swagger)
  val datasetController       = new DatasetController(datasetService, userDAO, swagger)
  val datasetFieldController  = new DatasetFieldController(datasetFieldService, userDAO, swagger)
  val dataUseController       = new DataUseController(dataUseService, userDAO, swagger)
  val dataQualifierController = new DataQualifierController(dataQualifierService, userDAO, swagger)
  val dataCategoryController  = new DataCategoryController(dataCategoryService, userDAO, swagger)
  val dataSubjectController   = new DataSubjectController(dataSubjectService, userDAO, swagger)
  val policyController        = new PolicyController(policyService, userDAO, swagger)
  val policyRuleController    = new PolicyRuleController(policyRuleService, userDAO, swagger)
  val registryController      = new RegistryController(registryService, approvalService, daos, swagger)
  val userController          = new UserController(userService, userDAO, swagger)
  val adminController         = new AdminController(daos, swagger)
  val reportController        = new ReportController(reportService, userDAO, swagger)
  def stop(): Unit = {
    logger.info("Shutting down")
    DB.stop()
  }
}
