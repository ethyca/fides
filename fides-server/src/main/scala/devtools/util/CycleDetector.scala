package devtools.util

import com.typesafe.scalalogging.LazyLogging

import scala.collection.mutable.{HashSet => MSet, ArrayStack => MStack, ListBuffer => MBuffer}

/** Iterate through a node graoh expressed as a set of { String -> Set[String]}
  * and report if any loops exist in the graph. */
object CycleDetector extends LazyLogging {

  private class Node(
    val id: String,
    val children: MSet[Node],
    var visited: Boolean = false,
    var beingVisited: Boolean = false
  ) {}

  type NodeValue = (String, Set[String])
  /** List of { key , Set(keys) } -> Map{key -> Nodes } */
  private def makeNodeGraph(nodeKeys: Iterable[NodeValue], messages: MBuffer[String]) = {
    val keys     = nodeKeys.map(_._1).toSet
    val children = nodeKeys.flatMap(_._2).toSet
    //check for missing parents referenced in children, not in key set
    val missing = children.diff(keys)
    if (missing.nonEmpty) {
      //just log; this error is reported from validation
      messages += s"""Cycle detection error: the referenced systems [${missing.mkString(
        ","
      )}] don't exist in the available systems."""
      //Map.empty
    }
    //else {
    val nodeMap: Map[String, Node] = keys.map(k => k -> new Node(k, new MSet, false, false)).toMap
    nodeKeys.foreach((t: (String, Set[String])) => {
      val n = nodeMap(t._1)
      t._2.foreach(childKey => {
        //allow for the possibility of a missing node
        nodeMap.get(childKey).foreach(n.children.add)
      })
    })

    nodeMap
  }

  private def recordErrorCycle(s: MStack[String], messages: MBuffer[String]): Unit = {
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
          messages += s"cyclic reference: ${out.mkString("->")}"
        }
      }
    }
  }

  private def hasCycle(node: Node, path: MStack[String], messages: MBuffer[String]): Boolean = {
    path.push(node.id)
    if (node.visited) {
      return false
    }

    node.beingVisited = true

    for (child <- node.children) {
      if (child.beingVisited) {
        path.push(child.id)
        recordErrorCycle(path, messages)
        return true
      } else if (hasCycle(child, path, messages)) {
        return true
      }
    }
    node.beingVisited = false
    node.visited = true
    false
  }

  /** this will return cycle errors as warning strings. */
  def collectCycleErrors(nodeKeys: Iterable[NodeValue]): Seq[String] = {
    val messages = new MBuffer[String]
    val nodeMap  = makeNodeGraph(nodeKeys, messages)
    // if (!errors.hasErrors) {
    nodeMap.values.map(hasCycle(_, MStack(), messages)).fold(false)((a, b) => a || b)
    // }
    messages
  }

}
