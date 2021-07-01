package devtools.domain

import devtools.domain.definition.{OrganizationId, VersionStamp, WithFidesKey}
import devtools.domain.policy.PrivacyDeclaration
import devtools.util.JsonSupport
import devtools.util.JsonSupport.{dumps, parseToObj}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class SystemObject(
  id: Long,
  organizationId: Long,
  registryId: Option[Long],
  fidesKey: String,
  versionStamp: Option[Long],
  metadata: Option[Map[String, Any]],
  name: Option[String],
  description: Option[String],
  systemType: Option[String],
  privacyDeclarations: Set[PrivacyDeclaration],
  systemDependencies: Set[String],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[SystemObject, Long] with VersionStamp with OrganizationId {
  override def withId(idValue: Long): SystemObject = this.copy(id = idValue)

}

object SystemObject {

  type Tupled =
    (
      Long,
      Long,
      Option[Long],
      String,
      Option[Long],
      Option[String],
      Option[String],
      Option[String],
      Option[String],
      String,
      String,
      Option[Timestamp],
      Option[Timestamp]
    )

  def toInsertable(s: SystemObject): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      s.registryId,
      sanitizeUniqueIdentifier(s.fidesKey),
      s.versionStamp,
      s.metadata.map(JsonSupport.dumps),
      s.name,
      s.description,
      s.systemType,
      dumps(s.privacyDeclarations),
      dumps(s.systemDependencies),
      s.creationTime,
      s.lastUpdateTime
    )

  def fromInsertable(t: Tupled): SystemObject =
    SystemObject(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      t._6.flatMap(JsonSupport.parseToObj[Map[String, Any]](_).toOption),
      t._7,
      t._8,
      t._9, //system type
      parseToObj[Set[PrivacyDeclaration]](t._10).get,
      parseToObj[Set[String]](t._11).get,
      t._12,
      t._13
    )

}
