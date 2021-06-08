package devtools.domain.definition

/** Domain Type that is partitioned by organization. */
trait OrganizationId {
  def organizationId: Long
}
