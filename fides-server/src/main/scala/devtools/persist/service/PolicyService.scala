package devtools.persist.service

import com.typesafe.scalalogging.LazyLogging
import devtools.App.policyDAO
import devtools.controller.RequestContext
import devtools.domain.policy.Policy
import devtools.persist.dao.DAOs
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.PolicyValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class PolicyService(daos: DAOs, policyRuleService: PolicyRuleService, val validator: PolicyValidator)(implicit
  val ec: ExecutionContext
) extends AuditingService[Policy](daos.policyDAO, daos.auditLogDAO, daos.organizationDAO, validator) with LazyLogging
  with UniqueKeySearch[Policy] {

  def orgId(p: Policy): Long = p.organizationId

  /** populate policy with policy rules */
  override def hydrate(p: Policy): Future[Policy] =
    p.rules match {
      case Some(_) => Future.successful(p)
      case _ =>
        daos.policyRuleDAO
          .runAction(daos.policyRuleDAO.query.filter(_.policyId === p.id).result)
          .map(rules => p.copy(rules = Some(rules)))

    }

  override def createAudited(record: Policy, versionStamp: Long, ctx: RequestContext): Future[Policy] =
    for {
      d: Policy <- policyDAO.create(record.copy(versionStamp = Some(versionStamp)))
      t <- record.rules match {
        case None => Future.successful(None)
        case Some(rules) =>
          Future
            .sequence(
              rules.map(r =>
                policyRuleService
                  .createValidated(r.copy(policyId = d.id, organizationId = record.organizationId), ctx)
              )
            )
            .map(t => Some(t))

      }
    } yield d.copy(rules = t)

  override def updateAudited(
    record: Policy,
    versionStamp: Long,
    previous: Policy,
    ctx: RequestContext
  ): Future[Option[Policy]] =
    daos.policyDAO.update(record.copy(versionStamp = Some(versionStamp))) flatMap {

      case Some(policy) if record.rules.isDefined =>
        for {
          _ <- daos.policyRuleDAO.delete(_.policyId === record.id)
          rules = record.rules.getOrElse(Seq())
          createdRules = rules.map(r =>
            policyRuleService.createValidated(r.copy(policyId = policy.id, organizationId = record.organizationId), ctx)
          )
          b <- Future.sequence(createdRules)
        } yield Some(policy.copy(rules = Some(b)))
      case a => Future.successful(a)
    }

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[Policy]] = {
    val base: Future[Option[Policy]] =
      daos.policyDAO.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)
    base.flatMap {
      case None         => Future.successful(None)
      case Some(policy) => hydrate(policy).map(Some(_))
    }
  }

}
