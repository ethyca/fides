package devtools.domain.definition

import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.collection.mutable.{Set => MSet}

final case class TestTree(
  id: Int,
  parentId: Option[Int],
  fidesKey: String,
  children: MSet[TestTree]
) extends TreeItem[TestTree, Int] {}

class TreeItemTest extends AnyFunSuite with BeforeAndAfterAll {

  /* Create a tree of the form:
   *
   *         1
   *     2      5
   *   3  4    6  7
   *
   *  */
  private val tree = TestTree(1, Some(1), "1", MSet[TestTree]())

  override def beforeAll(): Unit = {
    tree.children.add(
      TestTree(
        2,
        Some(1),
        "2",
        MSet[TestTree](TestTree(3, Some(2), "3", MSet[TestTree]()), TestTree(4, Some(2), "4", MSet[TestTree]()))
      )
    )

    tree.children.add(
      TestTree(
        5,
        Some(1),
        "5",
        MSet[TestTree](TestTree(6, Some(2), "6", MSet[TestTree]()), TestTree(7, Some(2), "7", MSet[TestTree]()))
      )
    )

  }

  test("test tree collect") {
    tree.collect(_.id % 2 == 0).map(_.id) shouldEqual MSet(2, 4, 6)

    //collect all children
    tree.collect(_ => true).map(_.id) shouldEqual MSet(1, 2, 3, 4, 5, 6, 7)
  }

  test("test tree find") {
    for (i <- 1 to 7) {
      tree.find(_.id == i).isDefined shouldEqual true
    }
    tree.find(_.id == 0).isDefined shouldEqual false
  }

  test("test exists") {

    for (i <- 1 to 7) {
      tree.exists(_.id == i) shouldEqual true
    }
    tree.exists(_.id == 0) shouldEqual false
  }

}
