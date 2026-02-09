import { Avatar, Button, Card, Icons, Space, SparkleIcon, Text } from "fidesui";
import NextLink from "next/link";
import { ReactNode } from "react";

import { SeverityGauge } from "~/features/common/progress/SeverityGauge";
import { nFormatter, pluralize } from "~/features/common/utils";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { useConfirmAllFields } from "./fields/useConfirmAllFields";
import { mapConfidenceBucketToSeverity } from "./fields/utils";

export interface ConfidenceCardItem {
  label: string;
  count: number;
  severity: ConfidenceBucket;
}

interface ConfidenceCardProps {
  item: ConfidenceCardItem;
  reviewHref: string;
  monitorId: string;
}

interface GetActionsParams {
  item: ConfidenceCardItem;
  reviewHref: string;
  onConfirmAll?: () => void;
}

const getActions = ({
  item,
  reviewHref,
  onConfirmAll,
}: GetActionsParams): ReactNode[] => {
  const actions: ReactNode[] = [
    <NextLink
      href={{
        pathname: reviewHref,
        query: { confidenceBucket: item.severity },
      }}
      passHref
      key={item.label}
    >
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
  if (item.severity === ConfidenceBucket.HIGH && onConfirmAll) {
    actions.push(
      <Button
        key="confirm"
        type="text"
        size="small"
        icon={<Icons.CheckmarkOutline />}
        aria-label={`Approve all ${item.label} fields`}
        onClick={onConfirmAll}
      >
        Approve
      </Button>,
    );
  }
  return actions;
};

export const ConfidenceCard = ({
  item,
  reviewHref,
  monitorId,
}: ConfidenceCardProps) => {
  const severity = mapConfidenceBucketToSeverity(item.severity);
  const { confirmAll } = useConfirmAllFields(monitorId);

  const handleConfirmAll = () => {
    confirmAll(item.severity, item.count);
  };

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
      actions={getActions({
        item,
        reviewHref,
        onConfirmAll: handleConfirmAll,
      })}
    />
  );
};
