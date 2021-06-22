package devtools.domain

import devtools.domain.enums.ApprovalStatus

import java.sql.Timestamp

/** One item in a by-time output report. This represents a generated for-display value and
  * doesn't correspond to a database object.
  */
final case class ReportLine(
  status: ApprovalStatus,
  timestamp: Timestamp,
  tag: Option[String],
  message: Option[String],
  action: String,
  details: Map[String, _]
) extends Ordered[ReportLine] {

  /** By default we will want reports to output sorted by time. */
  def compare(a: ReportLine): Int = timestamp.compareTo(a.timestamp)
}

object ReportLine {
  /** Generate a report line for display from an approval record. */
  def apply(approval: Approval): ReportLine =
    ReportLine(
      approval.status,
      approval.creationTime.getOrElse(new Timestamp(0)),
      approval.submitTag,
      approval.submitMessage,
      approval.action,
      approval.details.getOrElse(Map())
    )
}
