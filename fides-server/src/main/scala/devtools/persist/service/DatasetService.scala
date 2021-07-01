package devtools.persist.service

import devtools.App.datasetDAO
import devtools.controller.RequestContext
import devtools.domain.{Dataset, DatasetField}
import devtools.persist.dao.DAOs
import devtools.persist.service.definition.{AuditingService, UniqueKeySearch}
import devtools.validation.DatasetValidator
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetService(val daos: DAOs, val datasetFieldService: DatasetFieldService, val validator: DatasetValidator)(
  implicit val context: ExecutionContext
) extends AuditingService[Dataset](daos.datasetDAO, daos.auditLogDAO, daos.organizationDAO, validator)
  with UniqueKeySearch[Dataset] {

  /** retrieve an org id from the base type */
  override def orgId(t: Dataset): Long = t.organizationId

  override def hydrate(r: Dataset): Future[Dataset] =
    for {
      fields: Seq[DatasetField] <- daos.datasetFieldDAO.filter(_.datasetId === r.id)
    } yield r.copy(fields = Some(fields))

  override def createAudited(record: Dataset, versionStamp: Long, ctx: RequestContext): Future[Dataset] = {
    for {
      d: Dataset <- datasetDAO.create(record.copy(versionStamp = Some(versionStamp)))
      t <- record.fields match {
        case None => Future.successful(None)
        case Some(fields) =>
          Future
            .sequence(
              fields.map(fld => datasetFieldService.createValidated(fld.copy(datasetId = d.id), ctx))
            )
            .map(t => Some(t))
      }
    } yield d.copy(fields = t)
  }

  override def updateAudited(
    record: Dataset,
    versionStamp: Long,
    previous: Dataset,
    ctx: RequestContext
  ): Future[Option[Dataset]] =
    daos.datasetDAO.update(record.copy(versionStamp = Some(versionStamp))) flatMap {

      case Some(dataset) if record.fields.isDefined =>
        for {
          _ <- daos.datasetFieldDAO.delete(_.datasetId === record.id)
          fields        = record.fields.getOrElse(Set())
          createdFields = fields.map(r => datasetFieldService.createValidated(r.copy(datasetId = dataset.id), ctx))
          b <- Future.sequence(createdFields)
        } yield Some(dataset.copy(fields = Some(b.toSeq)))

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
