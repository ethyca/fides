package devtools.domain

import devtools.domain.definition.IdType
import devtools.util.JsonSupport.{dumps, parseToObj}

import java.sql.Timestamp

final case class DatasetField(
  id: Long,
  datasetId: Long,
  name: String,
  path: Option[String],
  description: Option[String],
  dataCategories: Option[Set[String]],
  dataQualifier: Option[String],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends IdType[DatasetField, Long] {
  override def withId(idValue: Long): DatasetField = this.copy(id = idValue)

  /** Collect the data categories that match a given data qualifier */
  def categoriesForQualifiers(qualifiers: Set[DataQualifierName]): Set[DataCategoryName] =
    dataQualifier match {
      case Some(q) if qualifiers.contains(q) => dataCategories.getOrElse(Set())
      case _                                 => Set()
    }
}
object DatasetField {

  type Tupled =
    (Long, Long, String, Option[String], Option[String], Option[String], Option[String], Option[Timestamp], Option[Timestamp])

  def toInsertable(s: DatasetField): Option[Tupled] =
    Some(
      s.id,
      s.datasetId,
      s.name,
      s.path,
      s.description,
      s.dataCategories.map(dumps(_)),
      s.dataQualifier,
      s.creationTime,
      s.lastUpdateTime
    )
  def fromInsertable(t: Tupled): DatasetField = {
    DatasetField(
      t._1,
      t._2,
      t._3,
      t._4,
      t._5,
      t._6.map(parseToObj[Set[String]](_).get),
      t._7,
      t._8,
      t._9
    )

  }
}
