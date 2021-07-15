package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.{Dataset, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Tables.{datasetFieldQuery, datasetQuery}
import devtools.util.Sanitization.sanitizeUniqueIdentifier
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
      .flatMap(_ => validateDatasets(sys, errors))
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
      errors.addWarning("no declarations specified")
    } else {
      /* All map keys must be valid members of a data category */
      validateDataCategories(
        sys.organizationId,
        sys.privacyDeclarations.getOrElse(Seq()).flatMap(_.dataCategories).toSet,
        errors
      )
      /* All use categories must be members of data use categories */
      validateDataUseCategories(
        sys.organizationId,
        sys.privacyDeclarations.getOrElse(Seq()).map(_.dataUse).toSet,
        errors
      )
      /* All declared qualifiers must be valid data dataQualifier members */
      validateQualifiers(
        sys.organizationId,
        sys.privacyDeclarations.getOrElse(Seq()).map(_.dataQualifier).toSet,
        errors
      )
      /* All declared data subjects must be valid members */
      validateDataSubjects(
        sys.organizationId,
        sys.privacyDeclarations.getOrElse(Seq()).flatMap(_.dataSubjects).toSet,
        errors
      )
      /* All declared fields must be valid members */
      /* Dataset and field declarations a can either be a dataset fidesKey name or a dataset fides Key . fieldName
      value.
       */
      validateDatasets(sys, errors)
    }
  }

  /** Require that all values listed as a dependent rawDatasets exist */
  def validateDatasets(sys: SystemObject, errors: MessageCollector): Future[Unit] = {
    // rawDatasets as declared in the privacy declarations. These may be of the form
    // "dataset" or "dataset.field"
    val datasetIdentifiers =
      sys.privacyDeclarations.getOrElse(Seq()).flatMap(_.datasetReferences).toSet

    // the actual names of just the dataset part for searching
    val datasetNames = datasetIdentifiers.map(Dataset.baseName)

    val query = for {
      (dataset, field) <-
        datasetQuery
          .filter(d => d.organizationId === sys.organizationId && d.fidesKey.inSet(datasetNames))
          .joinLeft(datasetFieldQuery)
          .on(_.id === _.datasetId)
    } yield (dataset.fidesKey, field.map(_.name))

    for {
      foundCompositeNames <- daos.datasetDAO.runAction(query.result).map { ts =>
        {
          ts.map {
            case (dsName, Some(fName)) => s"$dsName.$fName"
            case (dsName, None)        => dsName
          }.toSet
        }
      }
      foundBaseNames = foundCompositeNames.map(Dataset.baseName)

      diff = datasetIdentifiers.diff(foundCompositeNames ++ foundBaseNames)
      _ = if (diff.nonEmpty) {
        errors.addError(s"The values [$diff] given as dataset fidesKeys do not exist.")
      }

    } yield ()

  }

}
