import {
  AntFlex as Flex,
  AntProgress as Progress,
  AntProgressProps as ProgressProps,
  AntText as Text,
} from "fidesui";

import { capitalize } from "~/features/common/utils";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

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
  rounding: Math.ceil,
} as const;

type DynamicProgressProps = Pick<ProgressProps, "percent" | "strokeColor">;

const ConfidenceBucketClass: Record<ConfidenceBucket, string> = {
  low: "var(--fidesui-error)",
  medium: "var(--fidesui-warning)",
  high: "var(--fidesui-success)",
  manual: "",
};

const ConfidenceBucketPercent: Record<ConfidenceBucket, number> = {
  low: 30,
  medium: 60,
  high: 100,
  manual: 0,
};

export const classifierDynamicProps = (
  confidenceBucket: ConfidenceBucket,
): Readonly<DynamicProgressProps> => ({
  percent: ConfidenceBucketPercent[confidenceBucket],
  strokeColor: ConfidenceBucketClass[confidenceBucket],
});

export const ClassifierProgress = ({
  confidenceBucket,
}: {
  confidenceBucket: ConfidenceBucket;
}) => (
  <Flex gap="small" align="center">
    <Progress
      {...CLASSIFIER_PROGRESS_PROPS}
      {...classifierDynamicProps(confidenceBucket)}
    />
    <Text size="sm" type="secondary" className="font-normal">
      {capitalize(confidenceBucket)}
    </Text>
  </Flex>
);
