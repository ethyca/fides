package devtools.persist.service

import devtools.controller.RequestContext
import devtools.domain.{Approval, ReportLine}
import devtools.persist.dao.ApprovalDAO
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.{ExecutionContext, Future}

/** Generate report objects for system, registry, organization state. */
class ReportService(val approvalDAO: ApprovalDAO)(implicit val executionContext: ExecutionContext) {

  def systemReport(systemId: Long, ctx: RequestContext): Future[Seq[ReportLine]] =
    approvalDAO.filter(a => a.organizationId === ctx.organizationId && a.systemId === systemId).map {
      s: Seq[Approval] =>
        s.map(ReportLine.apply).sorted
    }

  def registryReport(registryId: Long, ctx: RequestContext): Future[Seq[ReportLine]] =
    approvalDAO.filter(a => a.organizationId === ctx.organizationId && a.registryId === registryId).map {
      s: Seq[Approval] =>
        s.map(ReportLine.apply).sorted
    }

  def organizationReport(ctx: RequestContext): Future[Seq[ReportLine]] =
    approvalDAO.filter(_.organizationId === ctx.organizationId).map { s: Seq[Approval] =>
      s.map(ReportLine.apply).sorted
    }
}
