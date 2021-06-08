package devtools.util

import com.typesafe.scalalogging.LazyLogging
import devtools.validation.MessageCollector

import scala.collection.mutable.{HashSet => MSet, ArrayStack => MStack}

object CycleDetector extends LazyLogging {

  private class Node(
    val id: String,
    val children: MSet[Node],
    var visited: Boolean = false,
    var beingVisited: Boolean = false
  ) {}

  type NodeValue = (String, Set[String])
  /** List of { key , Set(keys) } -> Map{key -> Nodes } */
  private def makeNodeGraph(nodeKeys: Iterable[NodeValue], errors: MessageCollector) = {
    val keys     = nodeKeys.map(_._1).toSet
    val children = nodeKeys.flatMap(_._2).toSet
    //check for missing parents referenced in children, not in key set
    val missing = children.diff(keys)
    if (missing.nonEmpty) {
      //just log; this error is reported from validation
      logger.error(s"""The referenced objects don't exist in the given values:${missing.mkString(",")}""")
      //Map.empty
    }
    //else {
    val nodeMap: Map[String, Node] = keys.map(k => k -> new Node(k, new MSet, false, false)).toMap
    nodeKeys.foreach((t: (String, Set[String])) => {
      val n = nodeMap(t._1)
      t._2.foreach(childKey => {
        //allow for the possibility of a missing node
        nodeMap.get(childKey).foreach(n.children.add(_))
      })
    })

    nodeMap
  }

  private def recordErrorCycle(s: MStack[String], errors: MessageCollector): Unit = {
    val out = new MStack[String]
    if (s.nonEmpty) {
      val head = s.pop()
      out.push(head)
      while (s.nonEmpty) {
        val next = s.pop()
        if (next != head) {
          out.push(next)
        } else {
          out.push(next)
          errors.addError(s"cyclic reference: ${out.mkString("->")}")
        }
      }
    }
  }
  private def hasCycle(node: Node, path: MStack[String], errors: MessageCollector): Boolean = {
    path.push(node.id)
    if (node.visited) {
      return false
    }

    node.beingVisited = true

    for (child <- node.children) {
      if (child.beingVisited) {
        path.push(child.id)
        recordErrorCycle(path, errors)
        return true
      } else if (hasCycle(child, path, errors)) {
        return true
      }
    }
    node.beingVisited = false
    node.visited = true
    false
  }

  def collectCycleErrors(nodeKeys: Iterable[NodeValue], errors: MessageCollector): Unit = {

    val nodeMap = makeNodeGraph(nodeKeys, errors)
    // if (!errors.hasErrors) {
    nodeMap.values.map(hasCycle(_, MStack(), errors)).fold(false)((a, b) => a || b)
    // }
  }

}
