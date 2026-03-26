import { Button, Flex, Input, Select, Table, Title } from "fidesui";
import { useMemo, useState } from "react";

import AddDatasetsModal from "./AddDatasetsModal";
import { MOCK_AVAILABLE_DATASETS } from "./mockData";
import type { PurposeDatasetAssignment } from "./types";

interface AssignedDatasetsSectionProps {
  datasets: PurposeDatasetAssignment[];
}

const columns = [
  {
    title: "Dataset",
    dataIndex: "dataset_name",
    key: "dataset_name",
    sorter: (a: PurposeDatasetAssignment, b: PurposeDatasetAssignment) =>
      a.dataset_name.localeCompare(b.dataset_name),
  },
  {
    title: "System",
    dataIndex: "system_name",
    key: "system_name",
    width: 180,
    sorter: (a: PurposeDatasetAssignment, b: PurposeDatasetAssignment) =>
      a.system_name.localeCompare(b.system_name),
  },
  {
    title: "Collections",
    dataIndex: "collection_count",
    key: "collection_count",
    width: 120,
    sorter: (a: PurposeDatasetAssignment, b: PurposeDatasetAssignment) =>
      a.collection_count - b.collection_count,
  },
];

const AssignedDatasetsSection = ({ datasets }: AssignedDatasetsSectionProps) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [localDatasets, setLocalDatasets] =
    useState<PurposeDatasetAssignment[]>(datasets);
  const [search, setSearch] = useState("");
  const [systemFilter, setSystemFilter] = useState<string | null>(null);

  const systemOptions = useMemo(() => {
    const systems = [...new Set(localDatasets.map((d) => d.system_name))];
    return systems.map((s) => ({ label: s, value: s }));
  }, [localDatasets]);

  const filtered = useMemo(
    () =>
      localDatasets.filter((d) => {
        const matchesSearch = d.dataset_name
          .toLowerCase()
          .includes(search.toLowerCase());
        const matchesSystem = !systemFilter || d.system_name === systemFilter;
        return matchesSearch && matchesSystem;
      }),
    [localDatasets, search, systemFilter],
  );

  const handleConfirm = (keys: string[]) => {
    const updated = keys
      .map((key) => {
        const existing = localDatasets.find(
          (d) => d.dataset_fides_key === key,
        );
        if (existing) return existing;
        const available = MOCK_AVAILABLE_DATASETS.find(
          (d) => d.dataset_fides_key === key,
        );
        if (!available) return null;
        return {
          dataset_fides_key: available.dataset_fides_key,
          dataset_name: available.dataset_name,
          system_name: available.system_name,
          collection_count: 0,
        };
      })
      .filter(Boolean) as PurposeDatasetAssignment[];
    setLocalDatasets(updated);
    setModalOpen(false);
  };

  return (
    <div>
      <Flex justify="space-between" align="center" className="mb-3">
        <Title level={5} className="!mb-0">
          Datasets assigned
        </Title>
        <Button size="small" type="default" onClick={() => setModalOpen(true)}>
          + Add datasets
        </Button>
      </Flex>
      <Flex gap="small" className="mb-3" justify="space-between">
        <Input
          placeholder="Search datasets..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="middle"
          style={{ width: 240 }}
        />
        <Select
          placeholder="All systems"
          options={systemOptions}
          value={systemFilter}
          onChange={setSystemFilter}
          allowClear
          size="middle"
          style={{ width: 180 }}
        />
      </Flex>
      <Table
        dataSource={filtered}
        columns={columns}
        size="small"
        pagination={false}
        rowKey="dataset_fides_key"
        scroll={{ y: 300 }}
      />
      <AddDatasetsModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        assignedKeys={localDatasets.map((d) => d.dataset_fides_key)}
      />
    </div>
  );
};

export default AssignedDatasetsSection;
