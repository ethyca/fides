package devtools.util

import devtools.Generators.{oneOf, smallSetOf}
import devtools.{App, Generators, TestUtils}
import devtools.domain.definition.{CanBeTree, IdType, OrganizationId, TreeItem}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.must.Matchers.contain
import org.scalatest.matchers.should.Matchers.convertToAnyShouldWrapper

import scala.collection.mutable.{Set => MSet, TreeSet => MTSet}
import scala.concurrent.{ExecutionContext, Future}

final case class Node(
  id: Long,
  parentId: Option[Long],
  organizationId: Long,
  fidesKey: String
) extends IdType[Node, Long] with CanBeTree[Long, NodeTree] with OrganizationId {
  override def withId(idValue: Long): Node = this.copy(id = idValue)

  def toTreeItem: NodeTree =
    NodeTree(
      id,
      parentId,
      fidesKey,
      MTSet[NodeTree]()(Ordering.by[NodeTree, Long](_.id))
    )
}

final case class NodeTree(
  id: Long,
  parentId: Option[Long],
  fidesKey: String,
  children: MSet[NodeTree]
) extends TreeItem[NodeTree, Long] {}

class TreeCacheTest extends AnyFunSuite with TestUtils with BeforeAndAfterAll {

  /*
   *
   * Test a deeply nested tree structure in  treeCache.
   * All calls will ignore organizationId.
   * Build a tree and a sample cache structured like
   *
   *  test data
   *                       a             ...             b       ...            c
   *           al                    ar
   *     all        alr         arl      arr
   *  alll allr  alrl alrr  , .....
   *
   *   */
  private val kg = for {
    top <- Set("A", "B", "C", "D")
    l2  <- Set("l", "m", "r")
    l3  <- Set("l", "m", "r")
    l4  <- Set("l", "m", "r")
    l5  <- Set("l", "m", "r")
  } yield top + l2 + l3 + l4 + l5

  private val subStrings                  = kg.flatMap(k => Set(k.take(1), k.take(2), k.take(3), k.take(4)))
  private val indexed: Set[(String, Int)] = (kg ++ subStrings).zipWithIndex
  private val idsByKey                    = indexed.map(t => t._1 -> t._2.toLong).toMap
  private val nodes =
    indexed.map((t: (String, Int)) => Node(t._2, idsByKey.get(t._1.take(t._1.length - 1)), 1, t._1)).toSeq
  private val keys = nodes.map(_.fidesKey)

  class TestTreeCache(val nodes: Seq[Node]) extends TreeCache[NodeTree, Node] {
    override implicit def executionContext: ExecutionContext = App.executionContext

    override def getAll(pagination: Pagination): Future[Seq[Node]] = Future.successful(nodes)

    override def findAllInOrganization(l: Long, pagination: Pagination): Future[Seq[Node]] = Future.successful(nodes)
  }

  private val cache = new TestTreeCache(nodes)
  override def beforeAll(): Unit = {
    cache.cacheBuildAll()
    //cache not getting built before test run
    while (cache.cacheGetRoots(1).isEmpty) {
      Thread.sleep(10)
    }
  }

  test("Test cache get roots") {
    cache.cacheGetRoots(1).map(_.fidesKey).toSet shouldEqual Set("A", "B", "C", "D")
  }

  test("Test cache find") {
    for (_ <- 1 to 10) {
      val randomKey = Generators.oneOf(keys)
      cache.cacheFind(1, randomKey).get.fidesKey shouldEqual randomKey
    }
  }

  test("test children of") {
    Set("A", "Ar", "Arr", "Arrr", "Arrrr").foreach(k => {
      val children = cache.childrenOfInclusive(1, k)
      children should contain(k)
      //proper children
      children.diff(Set(k)).foreach(child => child.startsWith(k))
    })

    //blank and missing kg return the empty set
    Set("", "xxxxx").foreach(k => cache.childrenOfInclusive(1, k) shouldEqual Set())
  }
  test("test parents of") {
    Set("A", "Ar", "Arr", "Arrr", "Arrrr").foreach(k => {
      val parents = cache.parentsOf(1, k)
      parents shouldNot contain(k)
      parents.foreach(p => k.startsWith(p))
    })

    //blank and missing kg return the empty set
    Set("", "xxxxx").foreach(k => cache.parentsOf(1, k) shouldEqual Set())
  }
  test("test diff") {
    for (_ <- 1 to 10) {
      //any value with its children does not show children in the diff
      val randomChildrenOfA = smallSetOf[String](1, 10, cache.childrenOfInclusive(1, "A").toSeq)
      val randomChildrenOfB = smallSetOf[String](1, 10, cache.childrenOfInclusive(1, "B").toSeq)
      val randomChildOfB    = oneOf(randomChildrenOfB.toSeq)
      cache.diff(1, Set("A"), randomChildrenOfA) shouldEqual Set()

      //any value with a child of another tree shows that other tree member
      cache.diff(1, Set("A"), randomChildrenOfA + randomChildOfB) shouldEqual Set(randomChildOfB)
    }

  }
  test("test merge and reduce") {

    cache.mergeAndReduce(1, Set("A", "Ar")) shouldEqual Set("A")
    cache.mergeAndReduce(1, Set("A", "Arr")) shouldEqual Set("A")
    cache.mergeAndReduce(1, Set("A", "Arr")) shouldEqual Set("A")
    cache.mergeAndReduce(1, Set("A", "Arrr")) shouldEqual Set("A")
    cache.mergeAndReduce(1, Set("A", "Arrrr")) shouldEqual Set("A")
    for (_ <- 1 to 10) {
      val randomKey = Generators.oneOf(keys)
      // merge children
      val properChildren = cache.childrenOfInclusive(1, randomKey).diff(Set(randomKey))
      cache.mergeAndReduce(1, smallSetOf(1, 10, properChildren.toSeq) + randomKey) shouldEqual Set(randomKey)

      //merge complete level to higher level
      if (randomKey.length < 5) { // exclude leaf level kg, they will have no proper children to tes
        cache.mergeAndReduce(1, properChildren) shouldEqual Set(randomKey)
      }
      //merge of anything with a full root set should just give us the full root set
      cache.mergeAndReduce(1, Set("A", "B", "C", "D") ++ smallSetOf(1, 10, keys)) shouldEqual Set("A", "B", "C", "D")
    }
  }
}
