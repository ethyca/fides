package devtools.persist.service

import devtools.domain.DatasetField
import devtools.persist.dao.definition.DAO
import devtools.persist.db.Tables.DatasetFieldQuery
import devtools.persist.service.definition.Service
import devtools.validation.DatasetFieldValidator

import scala.concurrent.ExecutionContext

class DatasetFieldService(dao: DAO[DatasetField, Long, DatasetFieldQuery], val validator: DatasetFieldValidator)(
  implicit val context: ExecutionContext
) extends Service[DatasetField, Long, DatasetFieldQuery](dao, validator)(context)
