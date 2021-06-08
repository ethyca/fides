package devtools.domain.policy

import devtools.domain.DataQualifierName
import devtools.domain.definition.{WithFidesKey, OrganizationId}
import devtools.domain.enums.{PolicyAction, PolicyValueGrouping}
import devtools.util.JsonSupport.{dumps, parseToObj}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class PolicyRule(
  id: Long,
  organizationId: Long,
  policyId: Long,
  fidesKey: String,
  name: Option[String],
  description: Option[String],
  dataCategories: PolicyValueGrouping,
  dataUses: PolicyValueGrouping,
  dataSubjectCategories: PolicyValueGrouping,
  dataQualifier: Option[DataQualifierName],
  action: PolicyAction,
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[PolicyRule, Long] with OrganizationId {
  /** Supply a copy of this object with an altered id. */
  override def withId(idValue: Long): PolicyRule = this.copy(id = idValue)

}
object PolicyRule {

  type Tupled = (
    Long,
    Long,
    Long,
    String,
    Option[String],
    Option[String],
    String,
    String,
    String,
    Option[String],
    String,
    Option[Timestamp],
    Option[Timestamp]
  )

  def toInsertable(s: PolicyRule): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      s.policyId,
      sanitizeUniqueIdentifier(s.fidesKey),
      s.name,
      s.description,
      dumps(s.dataCategories),
      dumps(s.dataUses),
      dumps(s.dataSubjectCategories),
      s.dataQualifier,
      s.action.toString,
      None,
      None
    )

  def fromInsertable(t: Tupled): PolicyRule =
    PolicyRule(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      t._6,
      parseToObj[PolicyValueGrouping](t._7).get,
      parseToObj[PolicyValueGrouping](t._8).get,
      parseToObj[PolicyValueGrouping](t._9).get,
      t._10,
      PolicyAction.fromString(t._11).get,
      t._12,
      t._13
    )

}
