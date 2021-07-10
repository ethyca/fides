package devtools.domain

import devtools.domain.definition.{WithFidesKey, VersionStamp}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class Organization(
  id: Long,
  fidesKey: String,
  versionStamp: Option[Long],
  name: Option[String],
  description: Option[String],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[Organization, Long] with VersionStamp {
  override def withId(idValue: Long): Organization = this.copy(id = idValue)
}

object Organization {
  type Tupled = (Long, String, Option[Long], Option[String], Option[String], Option[Timestamp], Option[Timestamp])
  def toInsertable(s: Organization): Option[Tupled] =
    Some(
      s.id,
      sanitizeUniqueIdentifier(s.fidesKey),
      s.versionStamp,
      s.name,
      s.description,
      s.creationTime,
      s.lastUpdateTime
    )

  def fromInsertable(t: Tupled): Organization = Organization(t._1, t._2, t._3, t._4, t._5, t._6, t._7)

}
