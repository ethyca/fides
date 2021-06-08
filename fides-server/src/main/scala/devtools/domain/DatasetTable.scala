package devtools.domain

import devtools.domain.definition.IdType
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import java.sql.Timestamp

final case class DatasetTable(
  id: Long,
  datasetId: Long,
  name: String,
  description: Option[String],
  fields: Option[Seq[DatasetField]],
  creationTime: Option[Timestamp],
  lastUpdateTime: Option[Timestamp]
) extends IdType[DatasetTable, Long] {
  override def withId(idValue: Long): DatasetTable = this.copy(id = idValue)

  /** Collect the data categories that match a given data qualifier for all fields */
  def categoriesForQualifiers(qualifiers: Set[DataQualifierName]): Set[DataCategoryName] =
    fields match {
      case Some(r) => r.flatMap(_.categoriesForQualifiers(qualifiers)).toSet
      case None    => Set()
    }
}
object DatasetTable {

  type Tupled = (Long, Long, String, Option[String], Option[Timestamp], Option[Timestamp])

  def toInsertable(s: DatasetTable): Option[Tupled] =
    Some(s.id, s.datasetId, sanitizeUniqueIdentifier(s.name), s.description, s.creationTime, s.lastUpdateTime)
  def fromInsertable(t: Tupled): DatasetTable = DatasetTable(t._1, t._2, t._3, t._4, None, t._5, t._6)

}
