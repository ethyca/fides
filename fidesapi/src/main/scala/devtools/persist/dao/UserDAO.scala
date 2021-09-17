package devtools.persist.dao

import devtools.domain.User
import devtools.persist.dao.definition.{AutoIncrementing, ByOrganizationDAO, DAO}
import devtools.persist.db.Tables.{UserQuery, userQuery}
import slick.jdbc.GetResult
import slick.jdbc.PostgresProfile.api._

import java.sql.Timestamp
import scala.concurrent.ExecutionContext

class UserDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[User, Long, UserQuery](userQuery) with AutoIncrementing[User, UserQuery]
  with ByOrganizationDAO[User, UserQuery] {

  override implicit def getResult: GetResult[User] =
    r =>
      User.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[String],
        r.<<?[String],
        r.<<[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )
  /** Search clause by string fields */
  override def searchInOrganizationAction[C <: Rep[_]](value: String): UserQuery => Rep[Option[Boolean]] = {
    t: UserQuery =>
      (t.userName like value) ||
      (t.firstName like value) ||
      (t.lastName like value) ||
      (t.role like value)
  }

}
