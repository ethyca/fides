package devtools
/**
  * Fides domain objects, which map directly to database tables.
  */
package object domain {

  /** Data category taxonomy value string */
  type DataCategoryName = String
  /** Data use taxonomy value string */
  type DataUseName = String
  /** Data qualifier taxonomy value string */
  type DataQualifierName = String
  /** Data subject taxonomy value string */
  type DataSubjectName = String
  /** String that should map to a defined dataset name. */
  type DatasetName = String

  type ErrorList = Seq[String]

  /** member in a parent object that can contain either a specified set of
    * primary key of the child values, or the actual child values themselves.
    */
  type OneToMany[PK, T] = Option[Either[Seq[PK], Seq[T]]]

}
