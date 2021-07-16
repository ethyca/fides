package devtools.domain

import devtools.domain.definition.{CanBeTree, OrganizationId, TreeItem, WithFidesKey}

import scala.collection.mutable

final case class DataQualifier(
  id: Long,
  parentId: Option[Long],
  organizationId: Long,
  fidesKey: String,
  name: Option[String],
  clause: Option[String],
  description: Option[String]
) extends WithFidesKey[DataQualifier, Long] with CanBeTree[Long, DataQualifierTree] with OrganizationId {
  override def withId(idValue: Long): DataQualifier = this.copy(id = idValue)

  def toTreeItem: DataQualifierTree =
    DataQualifierTree(
      id,
      parentId,
      fidesKey,
      name,
      clause.getOrElse(""),
      new mutable.TreeSet[DataQualifierTree]()(Ordering.by[DataQualifierTree, Long](_.id))
    )
}
object DataQualifier {

  def toInsertable(
    s: DataQualifier
  ): Option[(Long, Option[Long], Long, String, Option[String], Option[String], Option[String])] =
    Some(s.id, s.parentId, s.organizationId, s.fidesKey, s.name, s.clause, s.description)

  def fromInsertable(
    t: (Long, Option[Long], Long, String, Option[String], Option[String], Option[String])
  ): DataQualifier = DataQualifier(t._1, t._2, t._3, t._4, t._5, t._6, t._7)

}

final case class DataQualifierTree(
  id: Long,
  parentId: Option[Long],
  fidesKey: String,
  name: Option[String],
  clause: String,
  children: mutable.Set[DataQualifierTree]
) extends TreeItem[DataQualifierTree, Long] {}
