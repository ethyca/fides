package devtools.domain

import devtools.domain.definition.{IdType, OrganizationId}
import devtools.domain.enums.Role

import java.sql.Timestamp

final case class User(
  id: Long,
  organizationId: Long,
  userName: String,
  firstName: Option[String],
  lastName: Option[String],
  role: Role,
  apiKey: Option[String],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends IdType[User, Long] with OrganizationId {
  override def withId(idValue: Long): User = this.copy(id = idValue)
}

object User {

  type Tupled =
    (Long, Long, String, Option[String], Option[String], String, Option[String], Option[Timestamp], Option[Timestamp])

  def toInsertable(s: User): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      s.userName,
      s.firstName,
      s.lastName,
      s.role.toString,
      s.apiKey,
      None,
      None
    )

  def fromInsertable(t: Tupled): User =
    User(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      Role.fromString(t._6).get,
      t._7,
      t._8,
      t._9
    )

}
