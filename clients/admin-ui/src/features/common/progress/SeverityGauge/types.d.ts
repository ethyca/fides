import { ProgressProps } from "fidesui";

export type DynamicProgressProps = Pick<
  ProgressProps,
  "percent" | "strokeColor"
>;

export type Severity = "low" | "medium" | "high";

export interface SeverityGaugeProps extends ProgressProps {
  severity: Severity;
  labels?: Record<Severity, string>;
}
