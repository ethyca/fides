package devtools.domain

import devtools.domain.definition.{IdType, OrganizationId, VersionStamp}
import devtools.domain.enums.AuditAction
import devtools.util.JsonSupport.{dumps, loads}
import org.json4s.JValue

import java.sql.Timestamp

final case class AuditLog(
  id: Long,
  objectId: Long,
  organizationId: Long,
  versionStamp: Option[Long],
  userId: Long,
  action: AuditAction,
  typeName: String,
  fromValue: Option[JValue],
  toValue: Option[JValue],
  change: Option[JValue],
  creationTime: Option[Timestamp]
) extends IdType[AuditLog, Long] with OrganizationId with VersionStamp {
  override def withId(idValue: Long): AuditLog = this.copy(id = idValue)
}

object AuditLog {

  type Tupled = (
    Long,
    Long,
    Long,
    Option[Long],
    Long,
    String,
    String,
    Option[String],
    Option[String],
    Option[String],
    Option[Timestamp]
  )

  def toInsertable(s: AuditLog): Option[Tupled] =
    Some(
      s.id,
      s.objectId,
      s.organizationId,
      s.versionStamp,
      s.userId,
      s.action.toString,
      s.typeName,
      s.fromValue.map(dumps),
      s.toValue.map(dumps),
      s.change.map(dumps),
      None
    )

  def fromInsertable(t: Tupled): AuditLog =
    AuditLog(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      AuditAction.fromString(t._6).get,
      t._7,
      t._8.map(loads(_).get),
      t._9.map(loads(_).get),
      t._10.map(loads(_).get),
      t._11
    )

}
