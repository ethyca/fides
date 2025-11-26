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

import { ClassifierProgress } from "~/features/classifier/ClassifierProgress";
import { nFormatter, pluralize } from "~/features/common/utils";

interface ConfidenceCardItem {
  label: string;
  count: number;
  percent: number;
}

interface ConfidenceCardProps {
  item: ConfidenceCardItem;
  reviewHref: string;
}

export const ConfidenceCard = ({ item, reviewHref }: ConfidenceCardProps) => {
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
          <ClassifierProgress percent={item.percent} confidenceScore={null} />
        </Space>
      }
      actions={[
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
      ]}
    />
  );
};
