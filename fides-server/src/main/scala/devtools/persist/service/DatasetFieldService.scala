package devtools.persist.service

import devtools.domain.DatasetField
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.definition.DAO
import devtools.persist.db.Queries.{datasetFieldQuery, datasetQuery}
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.DatasetFieldValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetFieldService(dao: DAO[DatasetField, Long, _], val validator: DatasetFieldValidator)(implicit
  val context: ExecutionContext
) extends Service[DatasetField, Long](dao, validator)(context) with UniqueKeySearch[DatasetField] {

  /** Assuming the specification is provided in the form datasetName.fieldName, return Some(datasetName, fieldName) if possible. */
  def splitFieldName(s: String): Option[(String, String)] =
    s.indexOf('.') match {
      case -1 => None
      case n  => Some((s.substring(0, n), s.substring(n + 1)))
    }

  /** Match by table.field name */
  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DatasetField]] =
    splitFieldName(key) match {
      case Some((datasetName, fieldName)) =>
        val action = for {
          a <-
            datasetQuery
              .join(datasetFieldQuery)
              .on(_.id === _.datasetId)
              .filter(_._1.fidesKey === datasetName)
              .filter(_._1.organizationId === organizationId)
              .filter(_._2.name === fieldName)
        } yield a._2
        dao.db.run(action.result.headOption)

      case _ =>
        throw InvalidDataException("Use datasetName.fieldName to search for a dataset table by unique identifier")
    }

}
