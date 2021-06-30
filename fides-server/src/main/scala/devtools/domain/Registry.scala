package devtools.domain

import devtools.domain.definition._
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class Registry(
  id: Long,
  organizationId: Long,
  fidesKey: String,
  metadata: Map[String, Any],
  versionStamp: Option[Long],
  description: Option[String],
  systems: OneToMany[Long, SystemObject],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[Registry, Long] with VersionStamp with OrganizationId {
  override def withId(idValue: Long): Registry = this.copy(id = idValue)

}
object Registry {
  type Tupled = (Long, Long, String, Option[Long], Option[String], Option[String], Option[Timestamp], Option[Timestamp])
  def toInsertable(s: Registry): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      sanitizeUniqueIdentifier(s.fidesKey),
      s.versionStamp,
      s.name,
      s.description,
      s.creationTime,
      s.lastUpdateTime
    )

  def fromInsertable(t: Tupled): Registry = Registry(t._1, t._2, t._3, t._4, t._5, t._6, None, t._7, t._8)

}
