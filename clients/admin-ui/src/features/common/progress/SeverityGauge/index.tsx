import { Progress, Text } from "fidesui";

import { SEVERITY_PERCENT, SEVERITY_PROPS, SEVERITY_STYLE } from "./constants";
import type {
  DynamicProgressProps,
  Severity,
  SeverityGaugeProps,
} from "./types";

export const statusDynamicProps = (
  status: Severity,
): Readonly<DynamicProgressProps> => ({
  percent: SEVERITY_PERCENT[status],
  strokeColor: SEVERITY_STYLE[status],
});

export const SeverityGauge = ({
  severity,
  labels = {
    low: "Low",
    medium: "Medium",
    high: "High",
  },
  ...props
}: SeverityGaugeProps) => (
  <Progress
    {...SEVERITY_PROPS}
    {...statusDynamicProps(severity)}
    // eslint-disable-next-line react/no-unstable-nested-components
    format={() => (
      <Text size="sm" type="secondary" className="font-normal">
        {labels[severity]}
      </Text>
    )}
    {...props}
  />
);
