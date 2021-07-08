package devtools.domain

import devtools.domain.definition.IdType
import devtools.util.JsonSupport
import devtools.util.Sanitization.sanitizeUniqueIdentifier

final case class PrivacyDeclaration(
  id: Long,
  systemId: Long,
  /** A name field to make reporting clearer. */
  name: String,
  dataCategories: Set[DataCategoryName],
  dataUse: DataUseName,
  dataQualifier: DataQualifierName,
  dataSubjects: Set[DataSubjectName],
  /* Dataset or dataset.field references.
   * *These are the "use" references that will be echoed to the user.*/
  datasetReferences: Set[String]
) extends IdType[PrivacyDeclaration, Long] {
  /** Supply a copy of this object with an altered id. */
  override def withId(id: Long): PrivacyDeclaration = this.copy(id = id)
}
object PrivacyDeclaration {

  /** collection of mixture of dataset, dataset.field to the set of unique referenced
    * rawDatasets. e.g. [dataset1.f1, dataset2.f1, dataset2] => [dataset1, dataset2]
    */
  def extractDatasets(references: Iterable[String]): Set[String] = references.map(_.split('.')(0)).toSet

  type Tupled = (Long, Long, String, String, DataUseName, DataQualifierName, String, String, String)

  def toInsertable(s: PrivacyDeclaration): Option[Tupled] = {
    val datasetReferences = s.datasetReferences.map(sanitizeUniqueIdentifier)
    Some(
      s.id,
      s.systemId,
      s.name,
      JsonSupport.dumps(s.dataCategories),
      s.dataUse,
      s.dataQualifier,
      JsonSupport.dumps(s.dataSubjects),
      JsonSupport.dumps(datasetReferences),
      JsonSupport.dumps(extractDatasets(datasetReferences))
    )
  }

  def fromInsertable(t: Tupled): PrivacyDeclaration =
    PrivacyDeclaration(
      t._1,
      t._2,
      t._3,
      JsonSupport.parseToObj[Set[String]](t._4).get,
      t._5,
      t._6,
      JsonSupport.parseToObj[Set[String]](t._7).get,
      JsonSupport.parseToObj[Set[String]](t._8).get
    )

}
