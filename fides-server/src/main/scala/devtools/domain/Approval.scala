package devtools.domain

import devtools.domain.definition.{IdType, OrganizationId, VersionStamp}
import devtools.domain.enums.ApprovalStatus
import devtools.util.JsonSupport.{dumps, parseToObj}

import java.sql.Timestamp

final case class Approval(
  id: Long,
  organizationId: Long,
  systemId: Option[Long],
  registryId: Option[Long],
  userId: Long,
  versionStamp: Option[Long],
  action: String,
  status: ApprovalStatus,
  details: Option[Map[String, _]],
  messages: Option[Map[String, Iterable[String]]],
  creationTime: Option[Timestamp]
) extends IdType[Approval, Long] with OrganizationId with VersionStamp {
  override def withId(idValue: Long): Approval = this.copy(id = idValue)

  def isFailure: Boolean = status == ApprovalStatus.FAIL

  def isSuccess: Boolean = status == ApprovalStatus.PASS
}
object Approval {

  type Tupled =
    (
      Long,
      Long,
      Option[Long],
      Option[Long],
      Long,
      Option[Long],
      String,
      String,
      Option[String],
      Option[String],
      Option[Timestamp]
    )

  def toInsertable(s: Approval): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      s.systemId,
      s.registryId,
      s.userId,
      s.versionStamp,
      s.action,
      s.status.toString,
      s.details.map(dumps),
      s.messages.map(dumps),
      None
    )

  def fromInsertable(t: Tupled): Approval =
    Approval(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      t._6,
      t._7,
      ApprovalStatus.fromString(t._8).get,
      t._9.map(v => parseToObj[Map[String, Map[String, Set[String]]]](v).getOrElse(Map())),
      t._10.map(v => parseToObj[Map[String, Seq[String]]](v).getOrElse(Map())),
      t._11
    )

  def stamp(): String = java.util.UUID.randomUUID.toString
}
