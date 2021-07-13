package devtools.util

import com.github.blemale.scaffeine.{Cache, Scaffeine}
import com.typesafe.scalalogging.LazyLogging
import devtools.domain.definition.{CanBeTree, IdType, OrganizationId, TreeItem}
import devtools.exceptions.InvalidDataException

import scala.collection.mutable.{Set => MSet}
import scala.concurrent.duration._
import scala.concurrent.{ExecutionContext, Future}

/** A per-organization cache-ing of the taxonomy tree(s), which we anticipate will be very rarely
  * updated (and in fact don't yet have an api for updates/deletions).
  *
  * Note that this implementation does not make any provision for multiple servers; an update to one
  * of these objects on another server won't get caught here unless we implement some sort of RPC
  * to trigger cache refresh. We will ultimately need to move the cache to an external
  * implementation or implement some kind of synchronization
  */
trait TreeCache[V <: TreeItem[V, Long], BaseType <: IdType[BaseType, Long] with CanBeTree[Long, V] with OrganizationId]
  extends LazyLogging {

  implicit def executionContext: ExecutionContext

  /** Unlimited retrieval (should not be used directly in services). */
  def getAll: Future[Seq[BaseType]] = getAll(Pagination.unlimited)

  /** Retrieve all based on applied pagination limits. */
  def getAll(pagination: Pagination): Future[Seq[BaseType]]

  /** Find all based on organization id. */
  def findAllInOrganization(l: Long, pagination: Pagination): Future[Seq[BaseType]]

  /** Take a sequence of the base type (as represented in the db) and organize
    * into a map of tree values that will be stored in the cache.
    */
  private def toTree(values: Seq[BaseType]): Map[Long, V] = {
    val m: Map[Long, V] = values.map(c => c.id -> c.toTreeItem).toMap
    logger.info(s"building cache, ids=${m.keySet}")
    m.values.filter(!_.isRoot).foreach { v =>
      val parent: Option[V] = m.get(v.parentId.get)
      parent match {
        case None =>
          logger.warn(
            s"The parent of ${v.getClass.getSimpleName}(id=${v.id}, parentId=${v.parentId}) does not exist!"
          )

        case Some(p) => p.children.add(v)
      }
    }
    m
  }

  /** Cache-ing by organization id, since it's simpler to deal with the taxonomy trees as
    * a single unit than to retrieve values individually.
    */
  val caches: Cache[Long, Map[Long, V]] = {
    val loaderF: Long => Map[Long, V] = organizationId => {
      logger.info(s"rebuilding cache for organizationId $organizationId")
      toTree(waitFor(findAllInOrganization(organizationId, Pagination.unlimited)))
    }

    Scaffeine()
      .expireAfterWrite(10.hours)
      .evictionListener[Long, Map[Long, V]]((k, v, cause) => {
        logger.info(s"Cache eviction $k:$cause:${v.keys}"); cacheBuild(k)
      })
      .build[Long, Map[Long, V]](
        loaderF,
        None,
        None
      )
  }

  /** Return the entire cache. This method will attempt to reload data if nothing stored is found. If
    * no data is stored, it will hold an empty map.
    * All cache search and useage methods should route through here to ensure there's a cache check if
    * no data is found.
    */
  def cacheGetAll(organizationId: Long): Map[Long, V] = {
    caches.getIfPresent(organizationId) match {
      case Some(c) => c
      case None =>
        logger.info(s"reloading cache for organization $organizationId")
        val t: Map[Long, V] = toTree(waitFor(findAllInOrganization(organizationId, Pagination.unlimited)))
        caches.put(organizationId, t)
        t
    }
  }

  /** Build for all values. */
  def cacheBuildAll(): Unit = getAll.foreach(s => {
    val v: Map[Long, Seq[BaseType]] = s.groupBy(_.organizationId)
    v.foreach { case (orgId: Long, v: Seq[BaseType]) => caches.put(orgId, toTree(v)) }
  })

  /** Build for a single organization */
  def cacheBuild(organizationId: Long): Unit = {
    findAllInOrganization(organizationId, Pagination.unlimited).foreach(values =>
      caches.put(organizationId, toTree(values))
    )
  }

  def cacheDelete(organizationId: Long): Unit = caches.invalidate(organizationId)

  /** Return only the cache root values (that is, values where parentId == None) for a given organization. */
  def cacheGetRoots(organizationId: Long): Iterable[V] = cacheGetAll(organizationId).values.filter(_.isRoot)

  /** Find existing fides key in an organization. */
  def cacheFind(organizationId: Long, fidesKey: String): Option[V] =
    cacheGetAll(organizationId).values.find(_.fidesKey == fidesKey)

  /** True if the cache contains a value that returns true for this function. */
  def containsFidesKey(organizationId: Long, fidesKey: String): Boolean = cacheFind(organizationId, fidesKey).isDefined

  /** Retrieve cache value by id. */
  def cacheGet(organizationId: Long, k: Long): Option[V] =
    cacheGetAll(organizationId).get(k) match {
      case None => logger.info(s"Cache miss: did not find $k"); None
      case s    => s
    }

  /** Returns all children of this key (including this key).
    * If the key is not found, returns the empty set.
    */
  def childrenOfInclusive(organizationId: Long, key: String): Set[String] =
    cacheFind(organizationId, key) match {
      case Some(v) => v.collect(_ => true).map(_.fidesKey).toSet
      case None    => Set()
    }

  /** Returns all the parents of this key (not including this key)
    * If the key is not found, returns the empty set.
    */
  def parentsOf(organizationId: Long, key: String): Set[String] =
    cacheFind(organizationId, key) match {
      case Some(v) if !v.isRoot =>
        cacheGet(organizationId, v.parentId.get) match {
          case Some(parent) => parentsOf(organizationId, parent.fidesKey) + parent.fidesKey
          case None         => Set()
        }
      case _ => Set()
    }

  /** values in left that are not in right
    *
    * mergeAndReduce left
    * mergeAndReduce right
    *
    * value v in right where
    *    - v is not in left AND
    *    - v has no parent that is in Left
    */
  def diff(organizationId: Long, left: Set[String], right: Set[String]): Set[String] = {
    val r = mergeAndReduce(organizationId, right)
    val l = mergeAndReduce(organizationId, left)
    r.filterNot(key => l.contains(key) || l.intersect(parentsOf(organizationId, key)).nonEmpty)
  }

  /** Combine keys under the following rules:
    *
    * if a is a child of b, (a,b) => b
    * if we have (a,b,c) and (a,b,c) are all the children of d, (a,b,c) => d
    */

  def mergeAndReduce(organizationId: Long, keys: Set[String]): Set[String] = {
    {

      val byId: Map[Long, V]    = cacheGetAll(organizationId)
      val cache: Map[String, V] = byId.values.map(v => v.fidesKey -> v).toMap

      // if any keys are not a part of this type, fail immediately
      val missing: Set[String] = keys.filterNot(k => cache.contains(k))
      if (missing.nonEmpty) {
        throw InvalidDataException(s"""The keys ${missing.mkString(",")} do not belong to this type""")
      }

      /** Return (sibling set, parent) of a given key */
      def siblingsOf(key: String): (MSet[String], String) = {
        val node = cache(key)
        node.parentId match {
          case None => (MSet(), "")
          case Some(pid) =>
            byId.get(pid) match {
              case None             => throw InvalidDataException(s"""parent id $pid of $key not found""")
              case Some(parentNode) => (parentNode.children.map(c => c.fidesKey), parentNode.fidesKey)
            }
        }
      }

      def childrenOf(key: String): MSet[String] = cache(key).children.flatMap(_.collect(_ => true)).map(_.fidesKey)

      def removeAll(toRemove: MSet[String], from: MSet[String]): Unit = toRemove.foreach(k => from.remove(k))

      if (keys.size < 2) {
        keys
      } else {
        val mKeys: MSet[String] = MSet() ++ keys
        val startKeys           = mKeys

        //for all keys, remove any child keys at any level
        startKeys.foreach { k => removeAll(childrenOf(k), mKeys) }

        //replace any complete sets of children with the parent
        //continue to do this until there's no change
        var replaceChildren = true
        while (replaceChildren) {
          startKeys.foreach { k =>
            {
              val (siblings, parent) = siblingsOf(k)
              if (siblings.nonEmpty && siblings.subsetOf(keys)) {
                removeAll(siblings, mKeys)
                mKeys.add(parent)
              } else {
                replaceChildren = false
              }
            }
          }
        }
        mKeys.toSet
      }
    }
  }
}
