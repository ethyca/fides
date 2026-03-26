import { Button, Card, CloseOutlined, Col, Flex, Input, Row, Select, Text, Title } from "fidesui";
import { useMemo, useState } from "react";

import AssignSystemsPickerModal from "./AssignSystemsPickerModal";
import { MOCK_AVAILABLE_SYSTEMS } from "./mockData";
import type { PurposeSystemAssignment } from "./types";

interface AssignedSystemsSectionProps {
  systems: PurposeSystemAssignment[];
}

const VISIBLE_COUNT = 8;

const AssignedSystemsSection = ({ systems }: AssignedSystemsSectionProps) => {
  const [localSystems, setLocalSystems] =
    useState<PurposeSystemAssignment[]>(systems);
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const typeOptions = useMemo(() => {
    const types = [...new Set(localSystems.map((s) => s.system_type))];
    return types.map((t) => ({ label: t, value: t }));
  }, [localSystems]);

  const filtered = useMemo(
    () =>
      localSystems.filter((s) => {
        const matchesSearch = s.system_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesType = !typeFilter || s.system_type === typeFilter;
        return matchesSearch && matchesType;
      }),
    [localSystems, search, typeFilter],
  );

  const visible = expanded ? filtered : filtered.slice(0, VISIBLE_COUNT);
  const hiddenCount = filtered.length - VISIBLE_COUNT;

  const handleConfirm = (systemIds: string[]) => {
    const updated = systemIds
      .map((id) => {
        const existing = localSystems.find((s) => s.system_id === id);
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
    setLocalSystems(updated);
    setModalOpen(false);
  };

  return (
    <div>
      <Flex justify="space-between" align="center" className="mb-3">
        <Title level={5} className="!mb-0">
          Data consumers
        </Title>
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
        {visible.map((system) => (
          <Col key={system.system_id} span={6}>
            <Card
              size="small"
              style={{ backgroundColor: "#fafafa", cursor: "pointer", position: "relative" }}
              className="group transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
              onClick={() =>
                window.open(
                  `/systems/configure/${system.system_id}`,
                  "_self",
                )
              }
            >
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined style={{ fontSize: 10 }} />}
                className="!absolute right-1 top-1 hidden !h-5 !w-5 !min-w-0 group-hover:inline-flex"
                onClick={(e) => {
                  e.stopPropagation();
                  setLocalSystems((prev) =>
                    prev.filter((s) => s.system_id !== system.system_id),
                  );
                }}
              />
              <Text strong className="text-sm">
                {system.system_name}
              </Text>
              <br />
              <Text type="secondary" className="text-xs">
                {system.system_type}
              </Text>
            </Card>
          </Col>
        ))}
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
        assignedIds={localSystems.map((s) => s.system_id)}
      />
    </div>
  );
};

export default AssignedSystemsSection;
