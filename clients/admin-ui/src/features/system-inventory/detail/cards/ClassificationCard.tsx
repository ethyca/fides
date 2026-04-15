import { Card, Flex, Progress, Text } from "fidesui";

import type { MockClassification } from "../../types";

interface ClassificationCardProps {
  classification: MockClassification;
}

const ClassificationCard = ({ classification }: ClassificationCardProps) => {
  const total =
    classification.approved +
    classification.pending +
    classification.unreviewed;
  const approvedPercent =
    total > 0 ? Math.round((classification.approved / total) * 100) : 0;

  return (
    <Card
      title="Classification coverage"
      size="small"
      extra={
        <Text
          type="secondary"
          className="cursor-pointer text-xs hover:underline"
        >
          Review fields ›
        </Text>
      }
    >
      {total === 0 ? (
        <Text type="secondary">No classifications found</Text>
      ) : (
        <>
          <Flex justify="space-between" className="mb-2">
            <Text className="text-xs">{classification.approved} approved</Text>
            <Text className="text-xs">{classification.pending} pending</Text>
            <Text className="text-xs">
              {classification.unreviewed} unreviewed
            </Text>
          </Flex>
          <Progress
            percent={approvedPercent}
            showInfo={false}
            strokeColor="#5a9a68"
            className="mb-3"
          />
          {classification.categories.map((cat) => (
            <Flex key={cat.name} justify="space-between" className="py-1">
              <Text className="text-xs">{cat.name}</Text>
              <Text type="secondary" className="text-xs">
                {cat.fieldCount} fields &middot; {cat.approvedPercent}% approved
              </Text>
            </Flex>
          ))}
        </>
      )}
    </Card>
  );
};

export default ClassificationCard;
