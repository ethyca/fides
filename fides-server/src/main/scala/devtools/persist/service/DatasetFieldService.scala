package devtools.persist.service

import devtools.domain.DatasetField
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.definition.DAO
import devtools.persist.db.Queries.{datasetFieldQuery, datasetQuery}
import devtools.persist.db.Tables.DatasetFieldQuery
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.DatasetFieldValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetFieldService(dao: DAO[DatasetField, Long, DatasetFieldQuery], val validator: DatasetFieldValidator)(
  implicit val context: ExecutionContext
) extends Service[DatasetField, Long, DatasetFieldQuery](dao, validator)(context)
