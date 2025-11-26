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
  steps: 3,
  showInfo: false,
  strokeLinecap: "round",
  size: {
    width: 24,
    height: 8,
  },
} as const;

type DynamicProgressProps = Pick<ProgressProps, "percent" | "strokeColor">;

const getStrokeColor = (percent: number): string => {
  if (percent > 66) {
    return "var(--fidesui-success)";
  }
  if (percent > 33) {
    return "var(--fidesui-warning)";
  }
  return "var(--fidesui-error)";
};

export const classifierDynamicProps = (
  percent: number,
): Readonly<DynamicProgressProps> => ({
  percent,
  strokeColor: getStrokeColor(percent ?? 0),
});

type ConfidenceLevel = ConfidenceScoreRange | "medium";

export const percentToConfidenceScore = (percent: number): ConfidenceLevel => {
  if (percent > 66) {
    return ConfidenceScoreRange.HIGH;
  }
  if (percent > 33) {
    return "medium";
  }
  return ConfidenceScoreRange.LOW;
};

export const ClassifierProgress = ({
  percent,
  confidenceScore,
}: {
  percent: number;
  confidenceScore?: ConfidenceScoreRange | null;
}) => {
  return (
    percent > 0 && (
      <Flex gap="small" align="center">
        <Progress
          {...CLASSIFIER_PROGRESS_PROPS}
          {...classifierDynamicProps(percent)}
        />
        {confidenceScore !== null && (
          <Text size="sm" type="secondary" className="font-normal">
            {capitalize(confidenceScore ?? percentToConfidenceScore(percent))}
          </Text>
        )}
      </Flex>
    )
  );
};
