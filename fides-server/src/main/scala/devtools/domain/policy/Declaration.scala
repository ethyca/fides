package devtools.domain.policy

import devtools.domain._

final case class Declaration(
  /** A name field to make reporting clearer. */
  name: String,
  dataCategories: Set[DataCategoryName],
  dataUse: DataUseName,
  dataQualifier: DataQualifierName,
  dataSubjectCategories: Set[DataSubjectCategoryName]
)
