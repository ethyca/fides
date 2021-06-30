package devtools.domain

import devtools.domain.definition.{WithFidesKey, OrganizationId, VersionStamp}
import devtools.domain.policy.Declaration
import devtools.util.JsonSupport.{dumps, parseToObj}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class SystemObject(
  id: Long,
  organizationId: Long,
  registryId: Option[Long],
  metadata: Option[Map[String, Any]],
  fidesKey: String,
  versionStamp: Option[Long],
  //fidesSystemType: Option[String], (renamed)
  systemType: Option[String],
  //name: Option[String],
  description: Option[String],
  privacyDeclarations: Seq[Declaration],
  systemDependencies: Set[String],
  //datasets: Set[String],
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
      String,
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
      s.fidesSystemType,
      s.name,
      s.description,
      dumps(s.declarations),
      dumps(s.systemDependencies),
      dumps(s.datasets),
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
      t._6,
      t._7,
      t._8,
      parseToObj[Seq[Declaration]](t._9).get,
      parseToObj[Set[String]](t._10).get,
      parseToObj[Set[String]](t._11).get,
      t._12,
      t._13
    )

}
