package devtools.domain.policy

import devtools.domain._

final case class Declaration(
  dataCategories: Set[DataCategoryName],
  dataUse: DataUseName,
  dataQualifier: DataQualifierName,
  dataSubjectCategories: Set[DataSubjectCategoryName]
)
