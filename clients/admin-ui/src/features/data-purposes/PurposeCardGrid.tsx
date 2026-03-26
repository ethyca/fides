import { Col, Divider, Flex, Input, Row, Text, Title } from "fidesui";
import { useMemo, useState } from "react";

import PurposeCard from "./PurposeCard";
import { usePurposes } from "./usePurposes";

const DATA_USE_LABELS: Record<string, string> = {
  analytics: "Analytics",
  "marketing.advertising": "Marketing & Advertising",
  "essential.service.security": "Security & Fraud Prevention",
  "essential.service.operations": "Essential Services",
  improve: "Product Improvement",
};

const formatDataUse = (key: string): string =>
  DATA_USE_LABELS[key] ?? key;

const PurposeCardGrid = () => {
  const { purposes, getSummaries } = usePurposes();
  const summaries = getSummaries;
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
      {groups.map(([dataUse, items]) => (
        <div key={dataUse} className="mb-8">
          <Flex gap="middle" align="center" className="mb-2">
            <Title level={4} className="!mb-0">
              {formatDataUse(dataUse)}
            </Title>
            <Text type="secondary">
              {items.length} {items.length === 1 ? "purpose" : "purposes"}
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
      ))}
    </div>
  );
};

export default PurposeCardGrid;
