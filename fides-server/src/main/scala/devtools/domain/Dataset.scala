package devtools.domain

import devtools.domain.definition.{WithFidesKey, OrganizationId, VersionStamp}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class Dataset(
  id: Long,
  organizationId: Long,
  fidesKey: String,
  versionStamp: Option[Long],
  name: Option[String],
  description: Option[String],
  location: Option[String],
  datasetType: Option[String],
  tables: Option[Seq[DatasetTable]],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[Dataset, Long] with VersionStamp with OrganizationId {
  override def withId(idValue: Long): Dataset = this.copy(id = idValue)

  def categoriesForQualifiers(qualifiers: Set[DataQualifierName]): Set[DataCategoryName] =
    tables match {
      case Some(r) => r.flatMap(_.categoriesForQualifiers(qualifiers)).toSet
      case None    => Set()
    }
}
object Dataset {

  type Tupled = (
    Long,
    Long,
    String,
    Option[Long],
    Option[String],
    Option[String],
    Option[String],
    Option[String],
    Option[Timestamp],
    Option[Timestamp]
  )

  def toInsertable(s: Dataset): Option[Tupled] =
    Some(
      s.id,
      s.organizationId,
      sanitizeUniqueIdentifier(s.fidesKey),
      s.versionStamp,
      s.name,
      s.description,
      s.location,
      s.datasetType,
      s.creationTime,
      s.lastUpdateTime
    )
  def fromInsertable(t: Tupled): Dataset =
    Dataset(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      t._6,
      t._7,
      t._8,
      None,
      t._9,
      t._10
    )

}
