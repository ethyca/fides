import { Col, Divider, Flex, Input, Row, Text, Title } from "fidesui";
import { useMemo, useState } from "react";

import PurposeCard from "./PurposeCard";
import { formatDataUse } from "./purposeUtils";
import type { DataPurpose, PurposeSummary } from "./types";

interface PurposeCardGridProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
}

const PurposeCardGrid = ({ purposes, summaries }: PurposeCardGridProps) => {
  const [search, setSearch] = useState("");

  const filtered = useMemo(
    () =>
      purposes.filter((p) =>
        p.name.toLowerCase().includes(search.toLowerCase()),
      ),
    [purposes, search],
  );

  const groups = useMemo(() => {
    const map: Record<string, typeof filtered> = {};
    filtered.forEach((p) => {
      if (!map[p.data_use]) {
        map[p.data_use] = [];
      }
      map[p.data_use].push(p);
    });
    return Object.entries(map);
  }, [filtered]);

  return (
    <div>
      <Input
        placeholder="Search purposes..."
        value={search}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setSearch(e.target.value)
        }
        allowClear
        style={{ width: 300, marginBottom: 24 }}
      />
      {groups.map(([dataUse, items]) => {
        const groupSystemCount = items.reduce((sum, p) => {
          const s = summaries.find((su) => su.id === p.id);
          return sum + (s?.system_count ?? 0);
        }, 0);
        const groupDatasetCount = items.reduce((sum, p) => {
          const s = summaries.find((su) => su.id === p.id);
          return sum + (s?.dataset_count ?? 0);
        }, 0);

        return (
          <div key={dataUse} className="mb-8">
            <Flex gap="middle" align="center" className="mb-2">
              <Title level={4} className="!mb-0">
                {formatDataUse(dataUse)}
              </Title>
              <Text type="secondary" className="text-sm">
                {items.length}{" "}
                {items.length === 1 ? "purpose" : "purposes"} &middot;{" "}
                {groupSystemCount} systems &middot; {groupDatasetCount}{" "}
                datasets
              </Text>
            </Flex>
            <Divider className="!mt-0 mb-4" />
            <Row gutter={[16, 16]}>
              {items.map((p) => (
                <Col key={p.id} span={6}>
                  <PurposeCard
                    purpose={p}
                    summary={summaries.find((s) => s.id === p.id)}
                  />
                </Col>
              ))}
            </Row>
          </div>
        );
      })}
    </div>
  );
};

export default PurposeCardGrid;
