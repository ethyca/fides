package devtools.persist.service

import devtools.domain.DatasetField
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.definition.DAO
import devtools.persist.db.Queries.{datasetFieldQuery, datasetQuery, datasetTableQuery}
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.DatasetFieldValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetFieldService(dao: DAO[DatasetField, Long, _], val validator: DatasetFieldValidator)(implicit
  val context: ExecutionContext
) extends Service[DatasetField, Long](dao, validator)(context) with UniqueKeySearch[DatasetField] {
  /** Match by table.field name */
  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DatasetField]] = {

    key.split('.') match {
      case vals if vals.length == 3 =>
        val datasetName = vals(0)
        val tableName   = vals(1)
        val fieldName   = vals(2)
        val action = for {
          a <-
            datasetQuery
              .join(datasetTableQuery)
              .on(_.id === _.datasetId)
              .join(datasetFieldQuery)
              .on(_._2.id === _.datasetTableId)
              .filter(_._1._1.fidesKey === datasetName)
              .filter(_._1._1.organizationId === organizationId)
              .filter(_._1._2.name === tableName)
              .filter(_._2.name === fieldName)
        } yield a._2
        dao.db.run(action.result.headOption)

      case _ =>
        throw InvalidDataException("Use datatsetName.tableName to search for a dataset table by unique identifier")
    }
  }

}
