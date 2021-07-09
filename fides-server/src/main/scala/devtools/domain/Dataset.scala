package devtools.domain

import devtools.domain.definition.{OrganizationId, VersionStamp, WithFidesKey}
import devtools.util.JsonSupport
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class Dataset(
  id: Long,
  organizationId: Long,
  fidesKey: String,
  versionStamp: Option[Long],
  metadata: Option[Map[String, Any]],
  name: Option[String],
  description: Option[String],
  dataCategories: Option[Set[String]],
  dataQualifier: Option[String],
  location: Option[String],
  datasetType: Option[String],
  fields: Option[Seq[DatasetField]],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends WithFidesKey[Dataset, Long] with VersionStamp with OrganizationId {
  override def withId(idValue: Long): Dataset = this.copy(id = idValue)

  /** form a map of qualifier -> categories for a given embedded field. For fields in which this is not specified,
    * the dataset value is  used. If no values are specified, no values will appear in the map.
    */
  def qualifierCategoriesMapForField(f:DatasetField): Map[DataQualifierName, Set[DataCategoryName] = {
    val qualifier = if (f.dataQualifier.isDefined) f.dataQualifier else dataQualifier
    val categories = if (f.dataCategories.isDefined) f.dataCategories else dataCategories
    (qualifier, categories) match {
      case (Some(q), Some(c)) => Map(q -> c)
      case _ => Map()

    }
  }

  def qualifierCategoriesMap():Map[DataQualifierName, Set[DataCategoryName]] =
     fields.getOrElse(Seq()).map(qualifierCategoriesMapForField).fold(Map())(_ ++ _ )


  def getField(name:String):Option[DatasetField] = fields flatMap {
    f => f.find(_.name == name)
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
      s.metadata.map(JsonSupport.dumps),
      s.name,
      s.description,
      s.dataCategories.map(JsonSupport.dumps),
      s.dataQualifier,
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
      t._5.flatMap(JsonSupport.parseToObj[Map[String, Any]](_).toOption),
      t._6,
      t._7,
      t._8.flatMap(JsonSupport.parseToObj[Set[String]](_).toOption),
      t._9,
      t._10,
      t._11,
      None,
      t._12,
      t._13
    )

}
