import { Avatar, Button, Card, Icons, Space, SparkleIcon, Text } from "fidesui";
import { ReactNode } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
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
    <RouterLink
      href={{
        pathname: reviewHref,
        query: { confidence_bucket: item.severity },
      }}
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
    </RouterLink>,
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
