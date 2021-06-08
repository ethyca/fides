package devtools.persist.service

import devtools.controller.RequestContext
import devtools.domain.DatasetTable
import devtools.exceptions.InvalidDataException
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.{datasetQuery, datasetTableQuery}
import devtools.persist.db.Tables
import devtools.persist.service.definition.{Service, UniqueKeySearch}
import devtools.validation.DatasetTableValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetTableService(
  val daos: DAOs,
  val datasetFieldService: DatasetFieldService,
  val validator: DatasetTableValidator
)(implicit
  val context: ExecutionContext
) extends Service[DatasetTable, Long](daos.datasetTableDAO, validator)(context) with UniqueKeySearch[DatasetTable] {

  override def hydrate(r: DatasetTable): Future[DatasetTable] =
    daos.datasetFieldDAO
      .filter(_.datasetTableId === r.id)
      .map(fields => r.copy(fields = Some(fields)))

  override def createValidated(record: DatasetTable, ctx: RequestContext): Future[DatasetTable] = {
    for {
      d: DatasetTable <- super.createValidated(record, ctx)
      t <- record.fields match {
        case None => Future.successful(None)
        case Some(fields) =>
          Future
            .sequence(
              fields.map(field => datasetFieldService.createValidated(field.copy(datasetTableId = d.id), ctx))
            )
            .map(t => Some(t))
      }
    } yield d.copy(fields = t)
  }

  override def updateValidated(
    record: DatasetTable,
    previous: DatasetTable,
    ctx: RequestContext
  ): Future[Option[DatasetTable]] =
    daos.datasetTableDAO.update(record) flatMap {

      case Some(table) if record.fields.isDefined =>
        for {
          _ <- daos.datasetFieldDAO.delete(_.datasetTableId === record.id)
          fields        = record.fields.getOrElse(Set())
          createdFields = fields.map(r => datasetFieldService.createValidated(r.copy(datasetTableId = table.id), ctx))
          b <- Future.sequence(createdFields)
        } yield Some(table.copy(fields = Some(b.toSeq)))

      case a => Future.successful(a)
    }

  /** Match by table.field name */
  def findByUniqueKey(organizationId: Long, key: String): Future[Option[DatasetTable]] = {

    key.split('.') match {
      case vals if vals.length == 2 =>
        val datasetName = vals(0)
        val tableName   = vals(1)
        val action: Query[Tables.DatasetTableQuery, DatasetTable, Seq] = for {
          a <-
            datasetQuery
              .join(datasetTableQuery)
              .on(_.id === _.datasetId)
              .filter(_._2.name === tableName)
              .filter(_._1.fidesKey === datasetName)
              .filter(_._1.organizationId === organizationId)
              .map(_._2)
        } yield a
        dao.db.run(action.result.headOption)

      case _ =>
        throw InvalidDataException("Use datatsetName.tableName to search for a dataset table by unique identifier")
    }
  }
}
