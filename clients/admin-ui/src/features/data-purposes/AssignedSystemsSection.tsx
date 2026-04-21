import {
  Button,
  Card,
  CloseOutlined,
  Col,
  Flex,
  Icons,
  Input,
  Row,
  Select,
  Text,
  Title,
  Tooltip,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import AssignSystemsPickerModal from "./AssignSystemsPickerModal";
import { MOCK_AVAILABLE_SYSTEMS } from "./mockData";
import type {
  PurposeDatasetAssignment,
  PurposeSystemAssignment,
} from "./types";

interface AssignedSystemsSectionProps {
  systems: PurposeSystemAssignment[];
  datasets: PurposeDatasetAssignment[];
  definedCategories: string[];
  onSystemsChange: (next: PurposeSystemAssignment[]) => void;
}

const VISIBLE_COUNT = 8;

const AssignedSystemsSection = ({
  systems,
  datasets,
  definedCategories,
  onSystemsChange,
}: AssignedSystemsSectionProps) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const typeOptions = useMemo(() => {
    const types = [...new Set(systems.map((s) => s.system_type))];
    return types.map((t) => ({ label: t, value: t }));
  }, [systems]);

  const datasetCountBySystem = useMemo(() => {
    const counts = new Map<string, number>();
    datasets.forEach((d) => {
      counts.set(d.system_name, (counts.get(d.system_name) ?? 0) + 1);
    });
    return counts;
  }, [datasets]);

  const definedSet = useMemo(
    () => new Set(definedCategories),
    [definedCategories],
  );

  const riskBySystem = useMemo(() => {
    const map = new Map<string, string[]>();
    datasets.forEach((d) => {
      const undeclared = d.data_categories.filter((c) => !definedSet.has(c));
      if (undeclared.length === 0) return;
      const prior = map.get(d.system_name) ?? [];
      const merged = Array.from(new Set([...prior, ...undeclared]));
      map.set(d.system_name, merged);
    });
    return map;
  }, [datasets, definedSet]);

  const filtered = useMemo(
    () =>
      systems.filter((s) => {
        const matchesSearch = s.system_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesType = !typeFilter || s.system_type === typeFilter;
        return matchesSearch && matchesType;
      }),
    [systems, search, typeFilter],
  );

  const visible = expanded ? filtered : filtered.slice(0, VISIBLE_COUNT);
  const hiddenCount = filtered.length - VISIBLE_COUNT;

  const handleConfirm = (systemIds: string[]) => {
    const updatedSystems = systemIds
      .map((id) => {
        const existing = systems.find((s) => s.system_id === id);
        if (existing) return existing;
        const available = MOCK_AVAILABLE_SYSTEMS.find(
          (s) => s.system_id === id,
        );
        if (!available) return null;
        return {
          system_id: available.system_id,
          system_name: available.system_name,
          system_type: available.system_type,
          assigned: true,
        };
      })
      .filter(Boolean) as PurposeSystemAssignment[];
    onSystemsChange(updatedSystems);
    setModalOpen(false);
  };

  const handleRemoveSystem = (systemId: string) => {
    onSystemsChange(systems.filter((s) => s.system_id !== systemId));
  };

  return (
    <div>
      <Flex justify="space-between" align="flex-start" className="mb-3">
        <div>
          <Title level={5} className="!mb-1">
            Data consumers
          </Title>
          <Text type="secondary" className="text-xs">
            Systems and groups authorized to access data under this purpose.
          </Text>
        </div>
        <Button size="small" type="default" onClick={() => setModalOpen(true)}>
          + Add data consumers
        </Button>
      </Flex>
      <Flex gap="small" className="mb-3" justify="space-between">
        <Input
          placeholder="Search data consumers..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="middle"
          style={{ width: 240 }}
        />
        <Select
          placeholder="All types"
          options={typeOptions}
          value={typeFilter}
          onChange={setTypeFilter}
          allowClear
          size="middle"
          style={{ width: 180 }}
        />
      </Flex>
      <Row gutter={[12, 12]}>
        {visible.map((system) => {
          const datasetCount = datasetCountBySystem.get(system.system_name) ?? 0;
          const riskCategories = riskBySystem.get(system.system_name) ?? [];
          // Only surface the red indicator for BigQuery so the page tells a
          // focused story rather than flagging every at-risk consumer.
          const isAtRisk =
            system.system_name === "BigQuery" && riskCategories.length > 0;
          // Only show the dataset count on cards that actually have datasets
          // assigned via the purpose (BigQuery and Snowflake in the mock).
          const showDatasetCount =
            system.system_name === "BigQuery" ||
            system.system_name === "Snowflake";
          return (
            <Col key={system.system_id} span={6}>
              <Card
                size="small"
                style={{
                  backgroundColor: isAtRisk ? "#fff1f0" : "#fafafa",
                  cursor: "pointer",
                  position: "relative",
                  border: isAtRisk
                    ? `1px solid ${palette.FIDESUI_ERROR}`
                    : undefined,
                }}
                className="group transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
                onClick={() =>
                  window.open(
                    `/systems/configure/${system.system_id}`,
                    "_self",
                  )
                }
              >
                {showDatasetCount && (
                  <Text
                    type="secondary"
                    className="!absolute right-2 top-2 text-xs group-hover:hidden"
                  >
                    {datasetCount} {datasetCount === 1 ? "dataset" : "datasets"}
                  </Text>
                )}
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined style={{ fontSize: 10 }} />}
                  className="!absolute right-1 top-1 hidden !h-5 !w-5 !min-w-0 group-hover:inline-flex"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveSystem(system.system_id);
                  }}
                />
                <Flex align="center" gap={6}>
                  {isAtRisk && (
                    <Tooltip
                      title={`At risk: introduces undeclared ${riskCategories.length === 1 ? "category" : "categories"} (${riskCategories.join(", ")})`}
                    >
                      <span
                        style={{
                          color: palette.FIDESUI_ERROR,
                          lineHeight: 0,
                        }}
                      >
                        <Icons.WarningFilled size={14} />
                      </span>
                    </Tooltip>
                  )}
                  <Text strong className="text-sm">
                    {system.system_name}
                  </Text>
                </Flex>
                <div>
                  <Text type="secondary" className="text-xs">
                    {system.consumer_category === "group"
                      ? "Google group"
                      : system.system_type}
                  </Text>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>
      {!expanded && hiddenCount > 0 && (
        <Button
          type="link"
          size="middle"
          onClick={() => setExpanded(true)}
          className="mt-2 p-0"
        >
          See {hiddenCount} more
        </Button>
      )}
      {expanded && filtered.length > VISIBLE_COUNT && (
        <Button
          type="link"
          size="middle"
          onClick={() => setExpanded(false)}
          className="mt-2 p-0"
        >
          Show less
        </Button>
      )}
      <AssignSystemsPickerModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        assignedIds={systems.map((s) => s.system_id)}
      />
    </div>
  );
};

export default AssignedSystemsSection;
