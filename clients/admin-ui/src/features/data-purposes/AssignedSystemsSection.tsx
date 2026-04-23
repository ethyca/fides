import {
  Button,
  Card,
  CloseOutlined,
  Col,
  Empty,
  Flex,
  Icons,
  Input,
  Row,
  Select,
  Spin,
  Text,
  Title,
  Tooltip,
  useMessage,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";

import AssignPickerModal from "./AssignPickerModal";
import {
  type AvailableSystem,
  useAssignSystemsToPurposeMutation,
  useGetDataPurposeByKeyQuery,
  useGetPurposeAvailableSystemsQuery,
  useGetPurposeDatasetsQuery,
  useGetPurposeSystemsQuery,
  useRemoveSystemsFromPurposeMutation,
} from "./data-purpose.slice";

interface AssignedSystemsSectionProps {
  fidesKey: string;
}

const VISIBLE_COUNT = 8;

const AssignedSystemsSection = ({ fidesKey }: AssignedSystemsSectionProps) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const message = useMessage();
  const router = useRouter();

  const { data: purpose } = useGetDataPurposeByKeyQuery(fidesKey);
  const { data: systems = [], isLoading: isLoadingSystems } =
    useGetPurposeSystemsQuery(fidesKey);
  const { data: datasets = [] } = useGetPurposeDatasetsQuery(fidesKey);
  const [removeSystems] = useRemoveSystemsFromPurposeMutation();
  const { data: availableSystems = [], isFetching: isFetchingAvailable } =
    useGetPurposeAvailableSystemsQuery(fidesKey, { skip: !modalOpen });
  const [assignSystems, { isLoading: isAssigning }] =
    useAssignSystemsToPurposeMutation();

  const handleAssignSubmit = async (systemIds: string[]) => {
    const result = await assignSystems({ fidesKey, systemIds });
    if (isErrorResult(result)) {
      message.error("Could not assign systems");
      return false;
    }
    return true;
  };

  const definedCategories = purpose?.data_categories ?? [];

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
      if (undeclared.length === 0) {
        return;
      }
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

  const handleRemoveSystem = async (systemId: string) => {
    const result = await removeSystems({ fidesKey, systemIds: [systemId] });
    if (isErrorResult(result)) {
      message.error("Could not remove system");
    }
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
          aria-label="Filter by type"
          placeholder="All types"
          options={typeOptions}
          value={typeFilter}
          onChange={setTypeFilter}
          allowClear
          size="middle"
          style={{ width: 180 }}
        />
      </Flex>
      {isLoadingSystems && (
        <Flex justify="center" className="py-6">
          <Spin />
        </Flex>
      )}
      {!isLoadingSystems && systems.length === 0 && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No systems assigned yet"
        >
          <Button type="primary" onClick={() => setModalOpen(true)}>
            Assign systems
          </Button>
        </Empty>
      )}
      {!isLoadingSystems && systems.length > 0 && filtered.length === 0 && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No systems match your filters"
        />
      )}
      {!isLoadingSystems && filtered.length > 0 && (
        <>
          <Row gutter={[12, 12]}>
            {visible.map((system) => {
              const datasetCount =
                datasetCountBySystem.get(system.system_name) ?? 0;
              const riskCategories = riskBySystem.get(system.system_name) ?? [];
              const isAtRisk = riskCategories.length > 0;
              const showDatasetCount = datasetCount > 0;
              return (
                <Col key={system.system_id} span={6}>
                  <Card
                    size="small"
                    style={{
                      backgroundColor: isAtRisk ? "#fee2e2" : "#fafafa",
                      cursor: "pointer",
                      position: "relative",
                      border: isAtRisk
                        ? `1px solid ${palette.FIDESUI_ERROR}`
                        : undefined,
                    }}
                    className="group transition-shadow hover:shadow-[0_2px_6px_rgba(0,0,0,0.08)]"
                    onClick={() =>
                      router.push(`/systems/configure/${system.system_id}`)
                    }
                  >
                    {showDatasetCount && (
                      <Text
                        type="secondary"
                        className="!absolute right-2 top-2 text-xs group-hover:hidden"
                      >
                        {datasetCount}{" "}
                        {datasetCount === 1 ? "dataset" : "datasets"}
                      </Text>
                    )}
                    <Button
                      aria-label={`Remove ${system.system_name}`}
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
                            <Icons.WarningAltFilled size={14} />
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
        </>
      )}
      <AssignPickerModal<AvailableSystem>
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add data consumers"
        searchPlaceholder="Search data consumers..."
        filterPlaceholder="All types"
        data={availableSystems}
        isFetching={isFetchingAvailable}
        isSubmitting={isAssigning}
        columns={[
          { title: "System", dataIndex: "system_name", key: "system_name" },
          { title: "Type", dataIndex: "system_type", key: "system_type" },
        ]}
        getRowKey={(s) => s.system_id}
        getSearchValue={(s) => s.system_name}
        getFilterValue={(s) => s.system_type}
        onSubmit={handleAssignSubmit}
      />
    </div>
  );
};

export default AssignedSystemsSection;
