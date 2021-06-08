package devtools.util

import devtools.domain.{
  DataCategory,
  DataCategoryTree,
  DataQualifier,
  DataQualifierTree,
  DataSubjectCategory,
  DataSubjectCategoryTree,
  DataUse,
  DataUseTree
}

class Caches(
  val dataSubjectCategories: TreeCache[DataSubjectCategoryTree, DataSubjectCategory],
  val dataCategories: TreeCache[DataCategoryTree, DataCategory],
  val dataUses: TreeCache[DataUseTree, DataUse],
  val dataQualifiers: TreeCache[DataQualifierTree, DataQualifier]
) {}
