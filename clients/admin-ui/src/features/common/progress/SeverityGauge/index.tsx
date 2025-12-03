import {
  AntFlex as Flex,
  AntProgress as Progress,
  AntText as Text,
} from "fidesui";

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
  flexProps,
  textProps,
  progressProps,
}: SeverityGaugeProps) => (
  <Flex gap="small" align="center" {...flexProps}>
    <Progress
      {...SEVERITY_PROPS}
      {...statusDynamicProps(severity)}
      {...progressProps}
    />
    <Text size="sm" type="secondary" className="font-normal" {...textProps}>
      {labels[severity]}
    </Text>
  </Flex>
);
