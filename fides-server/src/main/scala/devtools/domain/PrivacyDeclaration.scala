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
  datasetReferences: Set[String]
) extends IdType[PrivacyDeclaration, Long] {
  /** Supply a copy of this object with an altered id. */
  override def withId(id: Long): PrivacyDeclaration = this.copy(id = id)
}
object PrivacyDeclaration {

  type Tupled = (Long, Long, String, String, DataUseName, DataQualifierName, String, String)

  def toInsertable(s: PrivacyDeclaration): Option[Tupled] =
    Some(
      s.id,
      s.systemId,
      s.name,
      JsonSupport.dumps(s.dataCategories),
      s.dataUse,
      s.dataQualifier,
      JsonSupport.dumps(s.dataSubjects),
      JsonSupport.dumps(s.datasetReferences.map(sanitizeUniqueIdentifier))
    )

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
