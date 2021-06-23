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
  /** A tag to be provided on submission, e.g. git commit tag */
  submitTag: Option[String],
  /** A message to be provided on submission, e.g. git commit message */
  submitMessage: Option[String],
  action: String,
  status: ApprovalStatus,
  details: Option[Map[String, _]],
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
      Option[String],
      Option[String],
      String,
      String,
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
      s.submitTag,
      s.submitMessage,
      s.action,
      s.status.toString,
      s.details.map(dumps),
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
      t._8,
      t._9,
      ApprovalStatus.fromString(t._10).get,
      t._11.map(v => parseToObj[Map[String, Map[String, Set[String]]]](v).getOrElse(Map())),
      t._12
    )

  def stamp(): String = java.util.UUID.randomUUID.toString
}
