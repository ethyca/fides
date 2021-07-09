package devtools.domain.definition
import scala.collection.mutable.{Set => MSet}
/** The item of type [[devtools.domain.definition.CanBeTree]] converted into a form where it is stored as a tree item (that
  * is, a member of tree with (possible) parent and child values.
  *
  * Root values are values with no parents.
  */
trait TreeItem[C <: TreeItem[C, PK], PK] {
  val id: PK
  val parentId: Option[PK]
  val fidesKey: String
  val children: MSet[C]
  /** An item is a root if there is no parent id defined. */
  def isRoot: Boolean = parentId.isEmpty

  /** All child values that match this predicate, including self */
  def collect(predicate: TreeItem[C, PK] => Boolean): MSet[TreeItem[C, PK]] = {
    val v: MSet[TreeItem[C, PK]] = children.flatMap({ c => c.collect(predicate) })
    if (predicate(this)) {
      v += this
    }
    v
  }

  /** A filtered copy of child values matching the given predicate. */
  def removeIf(predicate: TreeItem[C, PK] => Boolean): Unit = {
    children.filter(predicate).foreach(c => children.remove(c))
    children.foreach(c => c.removeIf(predicate))
  }

  /** Find first matching value from children, including self. */
  def find(predicate: TreeItem[C, PK] => Boolean): Option[TreeItem[C, PK]] = collect(predicate).headOption

  /** True if predicate matches some child, or self. */
  def exists(predicate: TreeItem[C, PK] => Boolean): Boolean = {
    if (predicate(this)) true
    else {
      children.exists(_.exists(predicate))
    }
  }

  /** The given fidesKey is one of the children of this node or is == to this node. */
  def containsChild(fidesKey:String) = exists(_.fidesKey == fidesKey)

}
/** Indicates a value that can be expressed and organized into a tree hierarchy.
  *
  * Our privacy taxonomy types are defined so that they can be All of our taxonomy types are defined this way so that we can make useful
  * inferences when one type is the child of another. This requires types to be defined with a parent as well as some kind of unique identifier
  * ( A fides key for our taxonomy types).
  *
  * These types are accessed via caching since we tend to need their place in the hierarchy (i.e. their related values).
  *
  * See [[devtools.util.TreeCache]]
  */
trait CanBeTree[PK, TreeItemType <: TreeItem[TreeItemType, PK]] {
  val id: PK
  val parentId: Option[PK]
  val organizationId: Long
  val fidesKey: String
  def toTreeItem: TreeItemType

}
