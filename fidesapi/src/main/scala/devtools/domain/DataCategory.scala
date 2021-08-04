package devtools.domain

import devtools.domain.definition.{CanBeTree, OrganizationId, TreeItem, WithFidesKey}

import scala.collection.mutable

final case class DataCategory(
  id: Long,
  parentId: Option[Long],
  organizationId: Long,
  fidesKey: String,
  name: Option[String],
  parentKey: Option[String],
  clause: Option[String],
  description: Option[String]
) extends WithFidesKey[DataCategory, Long] with CanBeTree[Long, DataCategoryTree] with OrganizationId {
  override def withId(idValue: Long): DataCategory = this.copy(id = idValue)

  def toTreeItem: DataCategoryTree =
    DataCategoryTree(
      id,
      parentId,
      fidesKey,
      name,
      parentKey,
      clause.getOrElse(""),
      mutable.TreeSet[DataCategoryTree]()(Ordering.by[DataCategoryTree, Long](_.id))
    )
}
object DataCategory {

  def toInsertable(
    s: DataCategory
  ): Option[(Long, Option[Long], Long, String, Option[String], Option[String], Option[String], Option[String])] =
    Some(s.id, s.parentId, s.organizationId, s.fidesKey, s.name, s.parentKey, s.clause, s.description)

  def fromInsertable(
    t: (Long, Option[Long], Long, String, Option[String], Option[String], Option[String], Option[String])
  ): DataCategory =
    DataCategory(t._1, t._2, t._3, t._4, t._5, t._6, t._7, t._8)

}

final case class DataCategoryTree(
  id: Long,
  parentId: Option[Long],
  fidesKey: String,
  name: Option[String],
  parentKey: Option[String],
  clause: String,
  children: mutable.Set[DataCategoryTree]
) extends TreeItem[DataCategoryTree, Long] {}
