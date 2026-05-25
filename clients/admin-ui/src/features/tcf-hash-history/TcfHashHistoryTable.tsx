import { format } from "date-fns";
import {
  Alert,
  Empty,
  Flex,
  Icons,
  Skeleton,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "fidesui";
import { type ComponentProps, useMemo } from "react";

import { usePagination } from "~/features/common/hooks";
import { InfinitePaginator } from "~/features/common/pagination/InfinitePaginator";
import {
  TcfDiff,
  TCFVersionHashHistoryResponse,
  useGetExperienceConfigTCFHashHistoryQuery,
} from "~/features/privacy-experience/privacy-experience.slice";

import { TRIGGER_SOURCE_COLORS, TRIGGER_SOURCE_LABELS } from "./constants";
import TcfHashDisplay from "./TcfHashDisplay";
import styles from "./TcfHashHistoryTable.module.scss";

interface Props {
  experienceConfigId: string;
}

type TagColor = ComponentProps<typeof Tag>["color"];
type ExpandIconFn = NonNullable<
  NonNullable<
    ComponentProps<typeof Table<TCFVersionHashHistoryResponse>>["expandable"]
  >["expandIcon"]
>;

type Chip = { label: string; type: "add" | "remove" | "change" };

function buildChangeChips(diff: TcfDiff | undefined): Chip[] {
  if (!diff) {
    return [];
  }
  const chips: Chip[] = [];
  const vendorsAdded = diff.vendors_added?.length ?? 0;
  const vendorsRemoved = diff.vendors_removed?.length ?? 0;
  const purposes =
    (diff.purposes_changed?.length ?? 0) +
    (diff.system_purposes_changed?.length ?? 0);
  const restrictions = diff.restrictions_changed?.length ?? 0;

  if (vendorsAdded) {
    chips.push({ label: `+${vendorsAdded} vendor`, type: "add" });
  }
  if (vendorsRemoved) {
    chips.push({ label: `−${vendorsRemoved} vendor`, type: "remove" });
  }
  if (purposes) {
    chips.push({ label: `${purposes} purpose`, type: "change" });
  }
  if (restrictions) {
    chips.push({ label: `${restrictions} restriction`, type: "change" });
  }
  return chips;
}

const CHIP_COLORS: Record<Chip["type"], TagColor> = {
  add: "success",
  remove: "error",
  change: "info",
};

const ChangesCell = ({ record }: { record: TCFVersionHashHistoryResponse }) => {
  const chips = buildChangeChips(record.details?.tcf_diff);
  if (!chips.length) {
    return (
      <Typography.Text type="secondary" className="text-xs">
        no diff recorded
      </Typography.Text>
    );
  }
  return (
    <Flex gap={4} wrap="wrap">
      {chips.map((chip) => (
        <Tag
          key={chip.label}
          color={CHIP_COLORS[chip.type]}
          className="m-0 text-xs"
        >
          {chip.label}
        </Tag>
      ))}
    </Flex>
  );
};

function formatContextKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatContextValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return value.join(", ") || "—";
  }
  return String(value);
}

type DiffItem = { label: string; variant: "add" | "remove" | "change" };

function buildDiffItems(diff: TcfDiff | undefined): DiffItem[] {
  if (!diff) {
    return [];
  }
  return [
    ...(diff.vendors_added ?? []).map(
      (id): DiffItem => ({ label: `Vendor ${id} added`, variant: "add" }),
    ),
    ...(diff.vendors_removed ?? []).map(
      (id): DiffItem => ({ label: `Vendor ${id} removed`, variant: "remove" }),
    ),
    ...(diff.systems_added ?? []).map(
      (id): DiffItem => ({ label: `System ${id} added`, variant: "add" }),
    ),
    ...(diff.systems_removed ?? []).map(
      (id): DiffItem => ({ label: `System ${id} removed`, variant: "remove" }),
    ),
    ...(diff.purposes_changed ?? []).map(
      (p): DiffItem => ({
        label: `V${p.vendor_id} P${p.purpose_id}: ${p.from ?? "none"} → ${p.to ?? "none"}`,
        variant: "change",
      }),
    ),
    ...(diff.system_purposes_changed ?? []).map(
      (p): DiffItem => ({
        label: `System ${p.system_id} P${p.purpose_id}: ${p.from ?? "none"} → ${p.to ?? "none"}`,
        variant: "change",
      }),
    ),
    ...(diff.restrictions_changed ?? []).map(
      (r): DiffItem => ({
        label: `Restriction P${r.purpose_id}/V${r.vendor_id}: ${r.from ?? "none"} → ${r.to ?? "none"}`,
        variant: "change",
      }),
    ),
  ];
}

const DIFF_ITEM_CLASS: Record<DiffItem["variant"], string> = {
  add: styles.diffItemAdd,
  remove: styles.diffItemRemove,
  change: styles.diffItemChange,
};

const TcfHashHistoryDetailPanel = ({
  record,
}: {
  record: TCFVersionHashHistoryResponse;
}) => {
  const ctx = record.details?.trigger_context;
  const diffItems = buildDiffItems(record.details?.tcf_diff);

  return (
    <Flex
      gap="large"
      className="px-8 py-4"
      style={{ background: "var(--fidesui-neutral-50, #f9fafb)" }}
    >
      {ctx && Object.keys(ctx).length > 0 && (
        <Flex vertical gap={4} className="min-w-[200px]">
          <Typography.Text
            type="secondary"
            className="text-xs font-semibold uppercase tracking-wider"
          >
            Trigger context
          </Typography.Text>
          {Object.entries(ctx).map(([key, val]) => (
            <Flex key={key} gap={6} align="baseline">
              <Typography.Text
                type="secondary"
                className="whitespace-nowrap text-xs"
              >
                {formatContextKey(key)}
              </Typography.Text>
              <Typography.Text className="text-xs font-medium">
                {formatContextValue(val)}
              </Typography.Text>
            </Flex>
          ))}
        </Flex>
      )}

      <Flex vertical gap={4} className="flex-1">
        <Typography.Text
          type="secondary"
          className="text-xs font-semibold uppercase tracking-wider"
        >
          Diff
          {diffItems.length > 0
            ? ` (${diffItems.length} change${diffItems.length === 1 ? "" : "s"})`
            : ""}
        </Typography.Text>
        {diffItems.length === 0 ? (
          <Typography.Text type="secondary" className="text-xs">
            No TCF data changes recorded.
          </Typography.Text>
        ) : (
          <Flex vertical gap={2}>
            {diffItems.map((item) => (
              <Flex
                key={item.label}
                align="center"
                gap={6}
                className={`rounded px-3 py-1 text-xs ${DIFF_ITEM_CLASS[item.variant]}`}
              >
                <span aria-hidden>•</span>
                <Typography.Text className="text-xs">
                  {item.label}
                </Typography.Text>
              </Flex>
            ))}
          </Flex>
        )}
      </Flex>
    </Flex>
  );
};

const renderExpandedRow = (record: TCFVersionHashHistoryResponse) => (
  <TcfHashHistoryDetailPanel record={record} />
);

const isRowExpandable = (record: TCFVersionHashHistoryResponse) =>
  !!(record.details?.trigger_context || record.details?.tcf_diff);

const expandIcon: ExpandIconFn = ({ expanded, onExpand, record }) => {
  const expandable = isRowExpandable(record);
  return (
    <button
      type="button"
      className={styles.expandBtn}
      onClick={expandable ? (e) => onExpand(record, e) : undefined}
      disabled={!expandable}
      aria-label={expanded ? "Collapse row" : "Expand row"}
    >
      {expanded ? (
        <Icons.CaretDown size={12} />
      ) : (
        <Icons.CaretRight size={12} />
      )}
    </button>
  );
};

const columns = [
  {
    title: "Date",
    dataIndex: "changed_at",
    key: "changed_at",
    render: (value: string) => (
      <Tooltip title={format(new Date(value), "PPpp")}>
        <Typography.Text className="text-xs">
          {format(new Date(value), "dd MMM yyyy, HH:mm")}
        </Typography.Text>
      </Tooltip>
    ),
  },
  {
    title: "Trigger",
    dataIndex: "trigger_source",
    key: "trigger_source",
    render: (value: string) => (
      <Tag color={TRIGGER_SOURCE_COLORS[value] ?? "default"}>
        {TRIGGER_SOURCE_LABELS[value] ?? value}
      </Tag>
    ),
  },
  {
    title: "Changes",
    key: "changes",
    render: (_: unknown, record: TCFVersionHashHistoryResponse) => (
      <ChangesCell record={record} />
    ),
  },
  {
    title: "Previous hash",
    dataIndex: "previous_hash",
    key: "previous_hash",
    render: (value: string | null | undefined) => (
      <TcfHashDisplay value={value} />
    ),
  },
  {
    title: "Current hash",
    dataIndex: "current_hash",
    key: "current_hash",
    render: (value: string | null | undefined) => (
      <TcfHashDisplay value={value} />
    ),
  },
];

const TcfHashHistoryTable = ({ experienceConfigId }: Props) => {
  const pagination = usePagination();
  const { pageIndex, pageSize } = pagination;

  const { data, isLoading, isError } =
    useGetExperienceConfigTCFHashHistoryQuery({
      experienceConfigId,
      page: pageIndex,
      size: pageSize,
    });

  const entries = useMemo(() => data?.items ?? [], [data]);

  if (isLoading) {
    return (
      <Flex vertical gap="middle">
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
        <Skeleton active paragraph={{ rows: 3 }} />
      </Flex>
    );
  }

  if (isError) {
    return <Alert type="error" title="Failed to load TCF hash history" />;
  }

  if (!entries.length) {
    return (
      <Empty
        image={<Icons.Time size={40} color="var(--fidesui-neutral-300)" />}
        imageStyle={{ height: "auto" }}
        description={
          <Flex vertical gap="small" align="center">
            <Typography.Text strong>
              No hash changes recorded yet
            </Typography.Text>
            <Typography.Text type="secondary" className="max-w-sm text-center">
              Hash changes are captured automatically whenever this TCF
              experience configuration is updated. They will appear here once
              the first change is made.
            </Typography.Text>
          </Flex>
        }
      />
    );
  }

  return (
    <Flex vertical gap="middle">
      <Table<TCFVersionHashHistoryResponse>
        columns={columns}
        dataSource={entries}
        rowKey="id"
        pagination={false}
        data-testid="tcf-hash-history-table"
        size="small"
        expandable={{
          expandedRowRender: renderExpandedRow,
          rowExpandable: isRowExpandable,
          expandIcon,
        }}
      />
      <InfinitePaginator
        disableNext={(data?.items?.length ?? 0) < pageSize}
        pagination={pagination}
      />
    </Flex>
  );
};

export default TcfHashHistoryTable;
