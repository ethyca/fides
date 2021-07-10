package devtools.domain.definition

/** Domain type with a tracked by-organization version stamp. */
trait VersionStamp {
  def versionStamp: Option[Long]
}
