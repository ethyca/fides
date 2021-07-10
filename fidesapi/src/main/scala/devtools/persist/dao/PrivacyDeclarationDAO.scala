package devtools.persist.dao

import devtools.domain._
import devtools.persist.dao.definition.{AutoIncrementing, DAO}
import devtools.persist.db.Tables.{PrivacyDeclarationQuery, privacyDeclarationQuery, systemQuery}
import devtools.util.JsonSupport
import devtools.util.Sanitization.sanitizeUniqueIdentifier
import slick.jdbc.GetResult
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class PrivacyDeclarationDAO(val db: Database)(implicit val executionContext: ExecutionContext)
  extends DAO[PrivacyDeclaration, Long, PrivacyDeclarationQuery](privacyDeclarationQuery)
  with AutoIncrementing[PrivacyDeclaration, PrivacyDeclarationQuery] {

  override implicit def getResult: GetResult[PrivacyDeclaration] =
    r =>
      PrivacyDeclaration.fromInsertable(
        r.<<[Long],
        r.<<[Long],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String],
        r.<<[String]
      )

  /* Find systems that reference any of the following taxonomy values, returning a list of corresponding fidesKeys.*/

  def systemsReferencingDataUse(organizationId: Long, dataUse: DataUseName): Future[Seq[String]] =
    db.run(
      systemQuery
        .join(privacyDeclarationQuery)
        .on(_.id === _.systemId)
        .filter(_._2.dataUse === dataUse)
        .filter(_._1.organizationId === organizationId)
        .map(_._1.fidesKey)
        .result
    )

  def systemsReferencingDataQualifier(organizationId: Long, dataQualifier: DataQualifierName): Future[Seq[String]] =
    db.run(
      systemQuery
        .join(privacyDeclarationQuery)
        .on(_.id === _.systemId)
        .filter(_._2.dataQualifier === dataQualifier)
        .filter(_._1.organizationId === organizationId)
        .map(_._1.fidesKey)
        .result
    )

  def systemsReferencingDataSubject(organizationId: Long, dataSubject: DataSubjectName): Future[Seq[String]] =
    findSystemsWithJsonArrayMember(organizationId, dataSubject, "data_subjects")

  def systemsReferencingDataCategory(organizationId: Long, dataCategory: DataCategoryName): Future[Seq[String]] =
    findSystemsWithJsonArrayMember(organizationId, dataCategory, "data_categories")

  def systemsReferencingDataset(organizationId: Long, dataset: String): Future[Seq[String]] =
    findSystemsWithJsonArrayMember(organizationId, dataset, "raw_datasets")

  /** search in json array field for any value with an existing key in the provided set. This applies to privacy_declaration.{data_categories, data_subjects, dataset_references}. */
  def findSystemsWithJsonArrayMemberIn(
    organizationId: Long,
    keys: Seq[String],
    memberName: String
  ): Future[Seq[String]] = {

    val sanitized = JsonSupport.dumps(keys.map(sanitizeUniqueIdentifier))

    db.run(
      sql"""select DISTINCT A.FIDES_KEY from SYSTEM_OBJECT A, PRIVACY_DECLARATION B where A.ORGANIZATION_ID = #$organizationId AND B.SYSTEM_ID = A.ID AND JSON_OVERLAPS('#$sanitized',B.#$memberName) > 0"""
        .as[String]
    )
  }

  /** search in json array field for any value with an existing key. This applies to privacy_declaration.{data_categories, data_subjects, dataset_references}. */
  def findSystemsWithJsonArrayMember(organizationId: Long, key: String, memberName: String): Future[Seq[String]] = {

    val sanitized = sanitizeUniqueIdentifier(key)
    db.run(
      sql"""select DISTINCT A.FIDES_KEY from SYSTEM_OBJECT A, PRIVACY_DECLARATION B where A.ORGANIZATION_ID = #$organizationId AND B.SYSTEM_ID = A.ID AND '#$sanitized' MEMBER OF (B.#$memberName)"""
        .as[String]
    )

  }
}
