import devtools.App
import org.scalatra._
import org.slf4j.{Logger, LoggerFactory}

import javax.servlet.ServletContext
import devtools.App._
class ScalatraBootstrap extends LifeCycle {
  val logger: Logger = LoggerFactory.getLogger(getClass)

  override def init(context: ServletContext): Unit = {

    context.mount(approvalController, "/v1/approval")
    context.mount(auditLogController, "/v1/audit-log")
    context.mount(organizationController, "/v1/organization")
    context.mount(systemController, "/v1/system")
    context.mount(datasetController, "/v1/dataset")
    context.mount(datasetTableController, "/v1/dataset-table")
    context.mount(datasetFieldController, "/v1/dataset-field")
    context.mount(dataUseController, "/v1/data-use")
    context.mount(dataSubjectCategoryController, "/v1/data-subject-category")
    context.mount(dataCategoryController, "/v1/data-category")
    context.mount(dataQualifierController, "/v1/data-qualifier")
    context.mount(policyController, "/v1/policy")
    context.mount(policyRuleController, "/v1/policy-rule")
    context.mount(registryController, "/v1/registry")
    context.mount(userController, "/v1/user")
    context.mount(swaggerServlet, "/v1/api-docs")
    context.mount(adminController, "/v1/admin")
    context.mount(reportController, "/v1/report")
  }

  override def destroy(context: ServletContext): Unit = {
    App.stop()
  }

}
