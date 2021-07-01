package devtools.persist.service

import devtools.App.datasetDAO
import devtools.controller.RequestContext
import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.DAOs
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DatasetValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetService(val daos: DAOs, val datasetTableService: DatasetTableService, val validator: DatasetValidator)(
  implicit val context: ExecutionContext
) extends AuditingService[Dataset](daos.datasetDAO, daos.auditLogDAO, daos.organizationDAO, validator)
  with UniqueKeySearch[Dataset] {

  /** retrieve an org id from the base type */
  override def orgId(t: Dataset): Long = t.organizationId

  override def hydrate(r: Dataset): Future[Dataset] = {
    val v: Future[(Seq[DatasetField])] = for {
      fields: Seq[DatasetField] <- daos.datasetFieldDAO.filter(_.datasetId.inSet(tables.map(t => t.id)))
    } yield fields

    v.map {
      case (tables, fields) =>
        val fieldsByTableId: Map[Long, Seq[DatasetField]] = fields.groupBy(_.datasetTableId)
        val tbls                                          = tables.map(t => t.copy(fields = fieldsByTableId.get(t.id)))
        r.copy(tables = Some(tbls))
    }
  }

  override def createAudited(record: Dataset, versionStamp: Long, ctx: RequestContext): Future[Dataset] = {
    for {
      d: Dataset <- datasetDAO.create(record.copy(versionStamp = Some(versionStamp)))
      t <- record.tables match {
        case None => Future.successful(None)
        case Some(tables) =>
          Future
            .sequence(
              tables.map(tbl => datasetTableService.createValidated(tbl.copy(datasetId = d.id), ctx))
            )
            .map(t => Some(t))

      }
    } yield d.copy(tables = t)
  }

  override def updateAudited(
    record: Dataset,
    versionStamp: Long,
    previous: Dataset,
    ctx: RequestContext
  ): Future[Option[Dataset]] =
    daos.datasetDAO.update(record.copy(versionStamp = Some(versionStamp))) flatMap {

      case Some(dataset) if record.tables.isDefined =>
        for {
          _ <- daos.datasetTableDAO.delete(_.datasetId === record.id)
          tables        = record.tables.getOrElse(Set())
          createdTables = tables.map(r => datasetTableService.createValidated(r.copy(datasetId = dataset.id), ctx))
          b <- Future.sequence(createdTables)
        } yield Some(dataset.copy(tables = Some(b.toSeq)))

      case a => Future.successful(a)
    }

  def findByUniqueKey(organizationId: Long, key: String): Future[Option[Dataset]] = {
    val base: Future[Option[Dataset]] =
      daos.datasetDAO.findFirst(t => t.fidesKey === key && t.organizationId === organizationId)
    base.flatMap {
      case None          => Future.successful(None)
      case Some(dataset) => hydrate(dataset).map(Some(_))
    }
  }
}
