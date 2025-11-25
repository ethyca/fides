import {
  AntFlexProps as FlexProps,
  AntProgressProps as ProgressProps,
  AntText as Text,
} from "fidesui";
import { ComponentProps } from "react";

export type DynamicProgressProps = Pick<
  ProgressProps,
  "percent" | "strokeColor"
>;

export type Severity = "low" | "medium" | "high";

export type SeverityGaugeProps = {
  severity: Severity;
  labels?: Record<Severity, string>;
  flexProps?: FlexProps;
  textProps?: ComponentProps<Text>;
  progressProps?: ProgressProps;
};
