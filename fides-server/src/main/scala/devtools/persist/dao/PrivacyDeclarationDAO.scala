package devtools.persist.dao

import devtools.domain.PrivacyDeclaration
import devtools.persist.dao.definition.{AutoIncrementing, DAO}
import devtools.persist.db.Queries.privacyDeclarationQuery
import devtools.persist.db.Tables.PrivacyDeclarationQuery
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.ExecutionContext

class PrivacyDeclarationDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[PrivacyDeclaration, Long, PrivacyDeclarationQuery](privacyDeclarationQuery)
  with AutoIncrementing[PrivacyDeclaration, PrivacyDeclarationQuery] {

  override implicit def getResult: GetResult[PrivacyDeclaration] =
    r =>
      PrivacyDeclaration.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String]
      )

}
