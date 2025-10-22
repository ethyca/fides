import {
  AntFlex as Flex,
  AntProgress as Progress,
  AntProgressProps as ProgressProps,
  AntText as Text,
} from "fidesui";

import { capitalize } from "~/features/common/utils";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";

export const CLASSIFIER_PROGRESS_PROPS: Readonly<ProgressProps> = {
  percentPosition: {
    align: "start",
    type: "outer",
  },
  steps: 2,
  showInfo: false,
  strokeLinecap: "round",
  size: {
    width: 24,
    height: 8,
  },
} as const;

type DynamicProgressProps = Pick<ProgressProps, "percent" | "strokeColor">;

export const classifierDynamicProps = (
  percent: number,
): Readonly<DynamicProgressProps> => ({
  percent,
  strokeColor:
    (percent ?? 0) > 50
      ? "var(--ant-color-success-text)"
      : "var(--ant-color-warning-text)",
});

export const percentToConfidenceScore = (percent: number) => {
  return percent > 50 ? ConfidenceScoreRange.HIGH : ConfidenceScoreRange.LOW;
};

export const ClassifierProgress = ({
  percent,
  confidenceScore,
}: {
  percent: number;
  confidenceScore?: ConfidenceScoreRange;
}) => {
  return (
    <Flex gap="small" align="center">
      <Progress
        {...CLASSIFIER_PROGRESS_PROPS}
        {...classifierDynamicProps(percent)}
      />
      <Text size="sm" type="secondary" className="font-normal">
        {capitalize(confidenceScore ?? percentToConfidenceScore(percent))}
      </Text>
    </Flex>
  );
};
