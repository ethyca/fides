package devtools.persist.dao

import devtools.domain.policy.{Policy, PolicyRule}
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{PolicyQuery, policyQuery, policyRuleQuery}
import slick.dbio.{Effect, NoStream}
import slick.jdbc.GetResult
import slick.jdbc.PostgresProfile.api._
import slick.lifted.CanBeQueryCondition
import slick.sql.FixedSqlAction

import java.sql.Timestamp
import scala.concurrent.{ExecutionContext, Future}

class PolicyDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[Policy, Long, PolicyQuery](policyQuery) with AutoIncrementing[Policy, PolicyQuery]
  with ByOrganizationDAO[Policy, PolicyQuery] {

  override def createAction(record: Policy): FixedSqlAction[Policy, NoStream, Effect.Write] =
    insertQuery += record.copy(id = 0, creationTime = None, lastUpdateTime = None)

  override implicit def getResult: GetResult[Policy] =
    r =>
      Policy.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[Long],
        r.<<?[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )
  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): PolicyQuery => Rep[Option[Boolean]] = {
    t: PolicyQuery =>
      (t.fidesKey like value) ||
      (t.name like value) ||
      (t.description like value)
  }

  /** retrieved all policies with populated policy rules that match the given filter */
  def findHydrated[C <: Rep[_]](
    expr: PolicyQuery => C
  )(implicit wt: CanBeQueryCondition[C]): Future[Iterable[Policy]] = {
    val q = for {
      (policy, rule) <- query.filter(expr) joinLeft policyRuleQuery on (_.id === _.policyId)
    } yield (policy, rule)

    db.run(q.result).map { pairs =>
      pairs.groupBy(t => t._1.id).values.map { s: Seq[(Policy, Option[PolicyRule])] =>
        s.head._1.copy(rules = Some(s.map(_._2).filter(_.isDefined).map(_.get)))
      }
    }
  }
}
