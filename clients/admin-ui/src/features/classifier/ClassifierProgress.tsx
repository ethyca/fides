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

/**
 * Placeholder for the classifier progress component.
 * TODO: Remove this when we have a proper confidence score from the backend and rename
 * the component below to ClassifierProgress.
 */
export const ClassifierProgress = ({
  percent,
  confidenceScore,
}: {
  percent: number;
  confidenceScore?: ConfidenceScoreRange;
}) => {
  // use fidesDebugger to keep Typescript happy about the params being passed in but not used
  fidesDebugger("percent", percent);
  fidesDebugger("confidenceScore", confidenceScore);
  return null;
};

/**
 * Future classifier progress component.
 * TODO: Rename this to ClassifierProgress when we have a proper confidence score from
 * the backend and remove the placeholder component above.
 */
export const FutureClassifierProgress = ({
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
