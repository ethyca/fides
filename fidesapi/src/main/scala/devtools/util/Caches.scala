package devtools.util

import devtools.domain.{
  DataCategory,
  DataCategoryTree,
  DataQualifier,
  DataQualifierTree,
  DataSubject,
  DataSubjectTree,
  DataUse,
  DataUseTree
}

class Caches(
  val dataSubjectCategories: TreeCache[DataSubjectTree, DataSubject],
  val dataCategories: TreeCache[DataCategoryTree, DataCategory],
  val dataUses: TreeCache[DataUseTree, DataUse],
  val dataQualifiers: TreeCache[DataQualifierTree, DataQualifier]
) {}
