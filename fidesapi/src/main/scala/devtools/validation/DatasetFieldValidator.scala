package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.DatasetField
import devtools.persist.dao.DAOs
import devtools.persist.db.Tables.{datasetFieldQuery, datasetQuery}
import devtools.util.Sanitization.isValidDatasetFieldReference
import slick.jdbc.PostgresProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class DatasetFieldValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[DatasetField, Long] with ValidateByTaxonomy {

  /** Qualifier exists
    * categories exist
    * datasetTableId exists
    */
  def validateForCreate(t: DatasetField, ctx: RequestContext): Future[Unit] = {

    val errors = new MessageCollector
    if (!isValidDatasetFieldReference(t.name)) {
      errors.addError(s"The field name ${t.name} is invalid")
    }
    val orgIdAction: Query[Rep[Long], Long, Seq] = for {
      a <-
        datasetQuery
          .join(datasetFieldQuery)
          .on(_.id === _.datasetId)
          .map(_._1)
          .map(_.organizationId)
    } yield a

    val v: Future[Option[Long]] = daos.datasetDAO.db.run(orgIdAction.result.headOption)
    v.flatMap {
      case Some(organizationId) =>
        t.dataCategories.foreach(c => validateDataCategories(organizationId, c, errors))
        t.dataQualifier.foreach(c => validateQualifiers(organizationId, Set(c), errors))
        Future.successful(errors)

      case None =>
        errors.addError(s"no parent organization/dataset found for field $t")
        Future.successful(errors)

    }.flatMap(_.asFuture())

  }

}
