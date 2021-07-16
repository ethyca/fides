package devtools.domain.policy
import devtools.domain.definition.{OrganizationId, VersionStamp, WithFidesKey}

import java.sql.Timestamp

final case class Policy(
  id: Long,
  organizationId: Long,
  fidesKey: String,
  versionStamp: Option[Long],
  name: Option[String],
  description: Option[String],
  rules: Option[Seq[PolicyRule]],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[Policy, Long] with OrganizationId with VersionStamp {

  /** Supply a copy of this object with an altered id. */
  override def withId(idValue: Long): Policy = this.copy(id = idValue)
}

object Policy {

  type Tupled = (Long, Long, String, Option[Long], Option[String], Option[String], Option[Timestamp], Option[Timestamp])

  def toInsertable(p: Policy): Option[Tupled] =
    Some(
      p.id,
      p.organizationId,
      p.fidesKey,
      p.versionStamp,
      p.name,
      p.description,
      p.creationTime,
      p.lastUpdateTime
    )

  def fromInsertable(t: Tupled): Policy = Policy(t._1, t._2, t._3, t._4, t._5, t._6, None, t._7, t._8)

}
