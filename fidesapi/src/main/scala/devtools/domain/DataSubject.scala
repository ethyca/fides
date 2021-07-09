package devtools.domain

import devtools.domain.definition.{CanBeTree, WithFidesKey, IdType, OrganizationId, TreeItem}
import devtools.util.Sanitization.sanitizeUniqueIdentifier

import scala.collection.mutable

final case class DataSubject(
  id: Long,
  parentId: Option[Long],
  organizationId: Long,
  fidesKey: String,
  name: Option[String],
  description: Option[String]
) extends WithFidesKey[DataSubject, Long] with CanBeTree[Long, DataSubjectTree] with OrganizationId {
  override def withId(idValue: Long): DataSubject = this.copy(id = idValue)

  def toTreeItem: DataSubjectTree =
    DataSubjectTree(
      id,
      parentId,
      fidesKey,
      name,
      new mutable.TreeSet[DataSubjectTree]()(Ordering.by[DataSubjectTree, Long](_.id))
    )
}

object DataSubject {
  type Tupled = (Long, Option[Long], Long, String, Option[String], Option[String])
  def toInsertable(s: DataSubject): Option[Tupled] =
    Some(s.id, s.parentId, s.organizationId, sanitizeUniqueIdentifier(s.fidesKey), s.name, s.description)

  def fromInsertable(t: Tupled): DataSubject =
    new DataSubject(t._1, t._2, t._3, t._4, t._5, t._6)

}
final case class DataSubjectTree(
  id: Long,
  parentId: Option[Long],
  fidesKey: String,
  name: Option[String],
  children: mutable.Set[DataSubjectTree]
) extends TreeItem[DataSubjectTree, Long] {}
