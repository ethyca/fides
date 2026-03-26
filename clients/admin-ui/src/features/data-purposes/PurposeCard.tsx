import { Card, Flex, Text } from "fidesui";
import { useRouter } from "next/router";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import type { DataPurpose, PurposeSummary } from "./types";

interface PurposeCardProps {
  purpose: DataPurpose;
  summary: PurposeSummary | undefined;
}

const getRelativeTime = (dateStr: string): string => {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Updated today";
  if (diffDays === 1) return "Updated yesterday";
  if (diffDays < 7) return `Updated ${diffDays} days ago`;
  if (diffDays < 30) return `Updated ${Math.floor(diffDays / 7)} weeks ago`;
  return `Updated ${Math.floor(diffDays / 30)} months ago`;
};

const PurposeCard = ({ purpose, summary }: PurposeCardProps) => {
  const router = useRouter();

  return (
    <Card
      size="small"
      style={{ backgroundColor: "#fafafa", cursor: "pointer", height: "100%" }}
      className="transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
      onClick={() => router.push(`${DATA_PURPOSES_ROUTE}/${purpose.id}`)}
    >
      <Flex vertical gap={8} className="h-full">
        <Text strong>{purpose.name}</Text>
        <Text type="secondary" className="line-clamp-2 text-xs">
          {purpose.description}
        </Text>
        <div className="mt-auto">
          <Text type="secondary" className="text-xs">
            {summary?.system_count ?? 0} data consumers &middot;{" "}
            {summary?.dataset_count ?? 0} datasets
          </Text>
          <br />
          <Text type="secondary" className="text-xs">
            {getRelativeTime(purpose.updated_at)}
          </Text>
        </div>
      </Flex>
    </Card>
  );
};

export default PurposeCard;
