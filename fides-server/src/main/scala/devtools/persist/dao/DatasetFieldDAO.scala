package devtools.persist.dao

import devtools.domain.DatasetField
import devtools.persist.dao.definition.{AutoIncrementing, DAO}
import devtools.persist.db.Queries.datasetFieldQuery
import devtools.persist.db.Tables.DatasetFieldQuery
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import java.sql.Timestamp
import scala.concurrent.ExecutionContext

class DatasetFieldDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[DatasetField, Long, DatasetFieldQuery](datasetFieldQuery)
  with AutoIncrementing[DatasetField, DatasetFieldQuery] {

  override implicit def getResult: GetResult[DatasetField] =
    r =>
      DatasetField.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )

}
