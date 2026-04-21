import { Input, Table, Tag } from "fidesui";
import NextLink from "next/link";
import { useMemo, useState } from "react";

import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";

import { usePurposes } from "./usePurposes";

interface PurposeRow {
  id: string;
  name: string;
  data_use: string;
  data_subject: string;
  system_count: number;
  dataset_count: number;
  category_count: number;
}

const columns = [
  {
    title: "Name",
    dataIndex: "name",
    key: "name",
    render: (name: string, record: PurposeRow) => (
      <NextLink href={`${DATA_PURPOSES_ROUTE}/${record.id}`}>
        <strong className="text-[var(--ant-color-primary)] hover:underline">
          {name}
        </strong>
      </NextLink>
    ),
    sorter: (a: PurposeRow, b: PurposeRow) => a.name.localeCompare(b.name),
  },
  {
    title: "Data use",
    dataIndex: "data_use",
    key: "data_use",
    render: (val: string) => val || <span className="text-gray-400">—</span>,
  },
  {
    title: "Subject",
    dataIndex: "data_subject",
    key: "data_subject",
    render: (val: string) => val || <span className="text-gray-400">—</span>,
  },
  {
    title: "Data consumers",
    dataIndex: "system_count",
    key: "system_count",
    sorter: (a: PurposeRow, b: PurposeRow) =>
      a.system_count - b.system_count,
  },
  {
    title: "Datasets",
    dataIndex: "dataset_count",
    key: "dataset_count",
    sorter: (a: PurposeRow, b: PurposeRow) =>
      a.dataset_count - b.dataset_count,
  },
  {
    title: "Categories",
    dataIndex: "category_count",
    key: "category_count",
    render: (count: number) => <Tag bordered={false}>{count}</Tag>,
  },
];

const PurposeTable = () => {
  const { purposes, getSummaries } = usePurposes();
  const summaries = getSummaries;
  const [search, setSearch] = useState("");

  const rows: PurposeRow[] = useMemo(
    () =>
      purposes.map((p) => {
        const summary = summaries.find((s) => s.id === p.id);
        return {
          id: p.id,
          name: p.name,
          data_use: p.data_use,
          data_subject: p.data_subjects?.[0] ?? "",
          system_count: summary?.system_count ?? 0,
          dataset_count: summary?.dataset_count ?? 0,
          category_count: p.data_categories.length,
        };
      }),
    [purposes, summaries],
  );

  const filtered = useMemo(
    () =>
      rows.filter((r) =>
        r.name.toLowerCase().includes(search.toLowerCase()),
      ),
    [rows, search],
  );

  return (
    <div>
      <Input
        placeholder="Search purposes..."
        value={search}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setSearch(e.target.value)
        }
        allowClear
        style={{ width: 300, marginBottom: 16 }}
      />
      <Table
        dataSource={filtered}
        columns={columns}
        rowKey="id"
        size="middle"
        pagination={false}
        tableLayout="auto"
      />
    </div>
  );
};

export default PurposeTable;
