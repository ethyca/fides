package devtools.persist.dao

import devtools.domain.DatasetTable
import devtools.persist.dao.definition.{AutoIncrementing, DAO}
import devtools.persist.db.Queries.datasetTableQuery
import devtools.persist.db.Tables.DatasetTableQuery
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import java.sql.Timestamp
import scala.concurrent.ExecutionContext

class DatasetTableDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[DatasetTable, Long, DatasetTableQuery](datasetTableQuery)
  with AutoIncrementing[DatasetTable, DatasetTableQuery] {

  override implicit def getResult: GetResult[DatasetTable] =
    r =>
      DatasetTable.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<?[String],
        r.<<?[Timestamp],
        r.<<?[Timestamp]
      )

}
