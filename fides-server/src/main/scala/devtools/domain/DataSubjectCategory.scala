package devtools.domain

import devtools.domain.definition.{CanBeTree, WithFidesKey, IdType, OrganizationId, TreeItem}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import scala.collection.mutable

final case class DataSubjectCategory(
  id: Long,
  parentId: Option[Long],
  organizationId: Long,
  fidesKey: String,
  name: Option[String],
  description: Option[String]
) extends WithFidesKey[DataSubjectCategory, Long] with CanBeTree[Long, DataSubjectCategoryTree] with OrganizationId {
  override def withId(idValue: Long): DataSubjectCategory = this.copy(id = idValue)

  def toTreeItem: DataSubjectCategoryTree =
    DataSubjectCategoryTree(
      id,
      parentId,
      fidesKey,
      name,
      new mutable.TreeSet[DataSubjectCategoryTree]()(Ordering.by[DataSubjectCategoryTree, Long](_.id))
    )
}

object DataSubjectCategory {
  type Tupled = (Long, Option[Long], Long, String, Option[String], Option[String])
  def toInsertable(s: DataSubjectCategory): Option[Tupled] =
    Some(s.id, s.parentId, s.organizationId, sanitizeUniqueIdentifier(s.fidesKey), s.name, s.description)

  def fromInsertable(t: Tupled): DataSubjectCategory =
    new DataSubjectCategory(t._1, t._2, t._3, t._4, t._5, t._6)

}
final case class DataSubjectCategoryTree(
  id: Long,
  parentId: Option[Long],
  fidesKey: String,
  name: Option[String],
  children: mutable.Set[DataSubjectCategoryTree]
) extends TreeItem[DataSubjectCategoryTree, Long] {}
