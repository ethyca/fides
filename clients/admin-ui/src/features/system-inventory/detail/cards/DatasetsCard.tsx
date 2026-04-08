import { Card, Descriptions, Text } from "fidesui";

import type { MockDataset } from "../../types";

interface DatasetsCardProps {
  datasets: MockDataset[];
  roles: Array<"producer" | "consumer">;
}

const DatasetsCard = ({ datasets, roles }: DatasetsCardProps) => {
  const totalCollections = datasets.reduce((s, d) => s + d.collectionCount, 0);
  const totalFields = datasets.reduce((s, d) => s + d.fieldCount, 0);
  const roleLabel = roles
    .map((r) => r.charAt(0).toUpperCase() + r.slice(1))
    .join(" + ");

  return (
    <Card
      title={
        <span className="text-[10px] uppercase tracking-wider">Datasets</span>
      }
      size="small"
    >
      {datasets.length === 0 ? (
        <Text type="secondary">No datasets linked</Text>
      ) : (
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Total">
            <Text strong>{datasets.length} datasets</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Collections">
            <Text strong>{totalCollections}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Fields">
            <Text strong>{totalFields}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Role">
            <Text strong>{roleLabel}</Text>
          </Descriptions.Item>
        </Descriptions>
      )}
    </Card>
  );
};

export default DatasetsCard;
