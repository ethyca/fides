import {
  AntAvatar as Avatar,
  AntButton as Button,
  AntCard as Card,
  AntSpace as Space,
  AntText as Text,
  Icons,
  SparkleIcon,
} from "fidesui";
import NextLink from "next/link";

import { SeverityGauge } from "~/features/common/progress/SeverityGauge";
import { nFormatter, pluralize } from "~/features/common/utils";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { ConfidenceLevelLabel } from "./constants";
import { mapConfidenceBucketToSeverity } from "./fields/utils";

interface ConfidenceCardItem {
  label: string;
  count: number;
  severity: ConfidenceBucket;
}

interface ConfidenceCardProps {
  item: ConfidenceCardItem;
  reviewHref: string;
}

const getActions = (item: ConfidenceCardItem, reviewHref: string) => {
  // TODO: [ENG-2000] update query params to include the confidence level
  const actions = [
    <NextLink href={reviewHref} passHref key={item.label}>
      <Button
        type="text"
        size="small"
        icon={<Icons.ListBoxes />}
        aria-label={`Review ${item.label} fields`}
      >
        Review
      </Button>
    </NextLink>,
  ];
  if (item.label === ConfidenceLevelLabel.HIGH) {
    // TODO: [ENG-2000] add confirm action
    actions.push(
      <Button
        type="text"
        size="small"
        icon={<Icons.CheckmarkOutline />}
        aria-label={`Confirm all ${item.label} fields`}
      >
        Confirm
      </Button>,
    );
  }
  return actions;
};

export const ConfidenceCard = ({ item, reviewHref }: ConfidenceCardProps) => {
  const severity = mapConfidenceBucketToSeverity(item.severity);

  return (
    <Card
      size="small"
      styles={{ body: { display: "none" } }}
      title={
        <Space>
          <Avatar size={24} icon={<SparkleIcon color="black" />} />
          <Text type="secondary" className="font-normal">
            {nFormatter(item.count)} {pluralize(item.count, "field", "fields")}
          </Text>
          <Text>{item.label}</Text>
          {severity && (
            <SeverityGauge severity={severity} format={() => null} />
          )}
        </Space>
      }
      actions={getActions(item, reviewHref)}
    />
  );
};
