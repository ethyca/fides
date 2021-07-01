package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.{DatasetName, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.datasetQuery
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class SystemValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[SystemObject, Long] with ValidateByTaxonomy with ValidateByOrganization {

  /** Perform any validations on the input object and collect any errors found. */
  def validateForCreate(sys: SystemObject, ctx: RequestContext): Future[Unit] = {
    val errors = new MessageCollector
    validateDeclarations(sys, errors)
    checkForSelfReference(sys, errors)
    requireOrganizationIdExists(sys.organizationId, errors)
      .flatMap(_ => validateRegistryExists(sys, errors))
      .flatMap(_ => errors.asFuture())
  }

  /** Disallow self-reference in referenced systems. */
  def checkForSelfReference(sys: SystemObject, errors: MessageCollector): Unit =
    if (sys.systemDependencies.contains(sys.fidesKey)) {
      errors.addError(s"Invalid self reference: System ${sys.fidesKey} cannot declare a dependency on itself")
    }

  /** If a registry id is specified, it must exist. */
  def validateRegistryExists(sys: SystemObject, errors: MessageCollector): Future[Unit] =
    sys.registryId match {
      case Some(rid) =>
        daos.registryDAO.exists(_.id === rid).map { exists =>
          if (!exists) {
            errors.addError("The referenced registry id does not exist")
          }
        }
      case _ => Future.unit
    }

  /** Validate each declaration for valid members. */
  def validateDeclarations(sys: SystemObject, errors: MessageCollector): Unit = {
    /*map cannot be empty */
    if (sys.privacyDeclarations.isEmpty) {
      errors.addError("no declarations specified")
    } else {
      /* All map keys must be valid members of a data category */
      validateDataCategories(sys.organizationId, sys.privacyDeclarations.flatMap(_.dataCategories).toSet, errors)
      /* All use categories must be members of data use categories */
      validateDataUseCategories(sys.organizationId, sys.privacyDeclarations.map(_.dataUse).toSet, errors)
      /* All declared qualifiers must be valid data dataQualifier members */
      validateQualifiers(sys.organizationId, sys.privacyDeclarations.map(_.dataQualifier).toSet, errors)
      /* All declared data subject categories must be valid members */
      validateDataSubjectCategories(sys.organizationId, sys.privacyDeclarations.flatMap(_.dataSubjects).toSet, errors)
    }
  }

  /** Require that all values listed as a dependent datasets exist */
  def validateDatasets(
    organizationId: Long,
    datasets: Set[DatasetName],
    errors: MessageCollector
  ): Future[Unit] = {
    val foundStrings: Future[Seq[String]] = daos.datasetDAO.runAction(
      datasetQuery
        .filter(d => d.organizationId === organizationId && d.fidesKey.inSet(datasets))
        .map(d => d.fidesKey)
        .result
    )
    foundStrings.map(f => {
      datasets
        .diff(f.toSet)
        .foreach(s => errors.addError(s"The value '$s' given as a dataset fidesKey does not exist."))
    })
  }

}
