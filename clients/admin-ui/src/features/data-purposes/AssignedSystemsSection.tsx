import {
  Button,
  Card,
  CloseOutlined,
  Col,
  Empty,
  Flex,
  Icons,
  Popconfirm,
  Row,
  Select,
  Spin,
  Text,
  Title,
  Tooltip,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { isErrorResult } from "~/features/common/helpers";
import styles from "~/features/data-purposes/AssignedSystemsSection.module.scss";

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

  const definedSet = useMemo(
    () => new Set(purpose?.data_categories ?? []),
    [purpose?.data_categories],
  );

  const typeOptions = useMemo(() => {
    const types = [...new Set(systems.map((system) => system.system_type))];
    return types.map((systemType) => ({
      label: systemType,
      value: systemType,
    }));
  }, [systems]);

  // Correlation by `system_name` assumes unique system display names.
  // `PurposeDatasetAssignment` doesn't currently expose `system_id`; once the
  // backend adds it, key these Maps by `system_id` instead.
  const datasetCountBySystem = useMemo(() => {
    const counts = new Map<string, number>();
    datasets.forEach((dataset) => {
      counts.set(
        dataset.system_name,
        (counts.get(dataset.system_name) ?? 0) + 1,
      );
    });
    return counts;
  }, [datasets]);

  const riskBySystem = useMemo(() => {
    const map = new Map<string, string[]>();
    datasets.forEach((dataset) => {
      const undeclared = dataset.data_categories.filter(
        (category) => !definedSet.has(category),
      );
      if (undeclared.length === 0) {
        return;
      }
      const prior = map.get(dataset.system_name) ?? [];
      const merged = Array.from(new Set([...prior, ...undeclared]));
      map.set(dataset.system_name, merged);
    });
    return map;
  }, [datasets, definedSet]);

  const filtered = useMemo(
    () =>
      systems.filter((system) => {
        const matchesSearch = system.system_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesType = !typeFilter || system.system_type === typeFilter;
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
      return;
    }
    message.success("System removed from purpose");
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
        <DebouncedSearchInput
          placeholder="Search data consumers..."
          value={search}
          onChange={setSearch}
          className="w-60"
        />
        <Select
          aria-label="Filter by type"
          placeholder="All types"
          options={typeOptions}
          value={typeFilter}
          onChange={setTypeFilter}
          allowClear
          size="middle"
          className="w-48"
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
                    hoverable
                    className={`${styles.consumerCard} ${isAtRisk ? styles.atRisk : ""}`}
                    onClick={() =>
                      router.push(`/systems/configure/${system.system_id}`)
                    }
                  >
                    {showDatasetCount && (
                      <Text
                        type="secondary"
                        className={`${styles.datasetCount} text-xs`}
                      >
                        {datasetCount}{" "}
                        {datasetCount === 1 ? "dataset" : "datasets"}
                      </Text>
                    )}
                    <Popconfirm
                      title={`Remove ${system.system_name} from this purpose?`}
                      okText="Remove"
                      cancelText="Cancel"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => handleRemoveSystem(system.system_id)}
                      onPopupClick={(event) => event.stopPropagation()}
                    >
                      <Button
                        aria-label={`Remove ${system.system_name}`}
                        type="text"
                        size="small"
                        icon={<CloseOutlined className={styles.removeIcon} />}
                        className={styles.removeButton}
                        onClick={(event) => event.stopPropagation()}
                      />
                    </Popconfirm>
                    <Flex align="center" gap={6}>
                      {isAtRisk && (
                        <Tooltip
                          title={`At risk: introduces undeclared ${riskCategories.length === 1 ? "category" : "categories"} (${riskCategories.join(", ")})`}
                        >
                          <span className={styles.warningIcon}>
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
        getRowKey={(system) => system.system_id}
        getSearchValue={(system) => system.system_name}
        getFilterValue={(system) => system.system_type}
        onSubmit={handleAssignSubmit}
      />
    </div>
  );
};

export default AssignedSystemsSection;
