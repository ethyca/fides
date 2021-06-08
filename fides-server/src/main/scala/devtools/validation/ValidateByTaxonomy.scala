package devtools.validation

import devtools.domain.{DataCategoryName, DataQualifierName, DataSubjectCategoryName, DataUseName}
import devtools.persist.dao.DAOs

import scala.concurrent.ExecutionContext

/** Validate the existence of taxonomy members */
trait ValidateByTaxonomy {

  val daos: DAOs
  implicit val executionContext: ExecutionContext

  /** Require that all values listed as a data subject category exist */
  def validateDataSubjectCategories(
    organizationId: Long,
    categories: Set[DataSubjectCategoryName],
    errors: MessageCollector
  ): Unit = {
    val foundStrings = daos.dataSubjectCategoryDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    categories
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data subject category does not exist."))
  }
  /** Require that all values listed as a data category exist */
  def validateDataCategories(
    organizationId: Long,
    categories: Set[DataCategoryName],
    errors: MessageCollector
  ): Unit = {
    val foundStrings = daos.dataCategoryDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    categories
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data category does not exist."))
  }

  /** Require that all values listed as a data use category exist */
  def validateDataUseCategories(organizationId: Long, uses: Set[DataUseName], errors: MessageCollector): Unit = {
    val foundStrings = daos.dataUseDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    uses
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data use category does not exist."))
  }

  /** Require that all values listed as a data dataQualifier exist */
  def validateQualifiers(organizationId: Long, qualifiers: Set[DataQualifierName], errors: MessageCollector): Unit = {
    val foundStrings = daos.dataQualifierDAO.cacheGetAll(organizationId).values.map(_.fidesKey).toSet
    qualifiers
      .diff(foundStrings)
      .foreach((s: String) => errors.addError(s"The value '$s' given as a data qualifier does not exist."))
  }

}
