import {
  Alert,
  Button,
  Card,
  Collapse,
  Divider,
  Empty,
  Flex,
  List,
  Skeleton,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  AccessPackageCategory,
  AccessPackageEntry,
  PrivacyRequestStatus,
  RedactionEntry,
  RedactionType,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { PrivacyRequestEntity } from "../types";
import {
  useApproveAccessPackageMutation,
  useGetAccessPackageQuery,
  useLazyDownloadAccessPackageQuery,
  useUpdateAccessPackageRedactionsMutation,
} from "./access-package.slice";

type Props = {
  subjectRequest: PrivacyRequestEntity;
};

const rowKeyFor = (e: AccessPackageEntry) =>
  `${e.source}::${e.record_index}::${e.field_path}`;

const entryToRedaction = (e: AccessPackageEntry): RedactionEntry => ({
  source: e.source,
  record_index: e.record_index,
  field_path: e.field_path,
  type: RedactionType.REDACT,
});

const renderValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

const CategoryTable = ({
  category,
  onSelectionChange,
  disabled,
}: {
  category: AccessPackageCategory;
  onSelectionChange: (
    category: AccessPackageCategory,
    selectedKeys: Set<string>,
  ) => void;
  disabled: boolean;
}) => {
  // Checked = included (not redacted). Unchecked = redacted.
  const selectedRowKeys = useMemo(
    () => category.entries.filter((e) => !e.redacted).map(rowKeyFor),
    [category.entries],
  );

  return (
    <Table<AccessPackageEntry>
      size="small"
      rowKey={rowKeyFor}
      dataSource={category.entries}
      pagination={false}
      rowSelection={{
        selectedRowKeys,
        onChange: (newSelectedKeys) =>
          onSelectionChange(category, new Set(newSelectedKeys as string[])),
        getCheckboxProps: () => ({ disabled }),
      }}
      columns={[
        {
          title: "Field",
          dataIndex: "field_path",
          key: "field_path",
          width: "30%",
          render: (v: string) => <code>{v}</code>,
        },
        {
          title: "Value",
          dataIndex: "value",
          key: "value",
          render: (_: unknown, record) => {
            if (record.redacted) {
              return <Tag color="error">Redacted</Tag>;
            }
            const text = renderValue(record.value);
            return (
              <Typography.Text
                ellipsis={{ tooltip: text }}
                className="max-w-[400px]"
              >
                {text}
              </Typography.Text>
            );
          },
        },
        {
          title: "System",
          key: "system",
          width: "25%",
          render: (_: unknown, record) =>
            record.system_name || record.system || record.source,
        },
      ]}
    />
  );
};

const PrivacyRequestDetailsAccessPackageTab = ({ subjectRequest }: Props) => {
  const message = useMessage();
  const privacyRequestId = subjectRequest.id;

  const { data, isLoading, error } = useGetAccessPackageQuery(privacyRequestId);
  const [updateRedactions, { isLoading: isSaving }] =
    useUpdateAccessPackageRedactionsMutation();
  const [approve, { isLoading: isApproving }] =
    useApproveAccessPackageMutation();
  const [downloadPackage, { isFetching: isDownloading }] =
    useLazyDownloadAccessPackageQuery();

  const isAwaitingReview =
    subjectRequest.status === PrivacyRequestStatus.AWAITING_ACCESS_REVIEW;

  const allEntries = useMemo<AccessPackageEntry[]>(() => {
    if (!data) {
      return [];
    }
    const entries: AccessPackageEntry[] = [];
    data.data_uses.forEach((du) =>
      du.categories.forEach((cat) => entries.push(...cat.entries)),
    );
    data.other?.categories.forEach((cat) => entries.push(...cat.entries));
    return entries;
  }, [data]);

  const totalFields = allEntries.length;
  const redactedCount = allEntries.filter((e) => e.redacted).length;
  const systemCount = useMemo(
    () => new Set(allEntries.map((e) => e.system || e.source)).size,
    [allEntries],
  );

  const handleCategorySelectionChange = useCallback(
    async (
      category: AccessPackageCategory,
      includedKeys: Set<string>, // checked rows = included = NOT redacted
    ) => {
      if (!data) {
        return;
      }
      const categoryKeys = new Set(category.entries.map(rowKeyFor));
      // Preserve redactions for entries NOT in this category, and any
      // non-redact actions on entries that are in this category.
      const preserved = data.redactions.filter((r) => {
        const k = `${r.source}::${r.record_index}::${r.field_path}`;
        return !categoryKeys.has(k) || r.type !== RedactionType.REDACT;
      });
      // Add redact entries for the rows in this category that are NOT
      // in the included set (i.e. unchecked = redacted).
      const added = category.entries
        .filter((e) => !includedKeys.has(rowKeyFor(e)))
        .map(entryToRedaction);
      const result = await updateRedactions({
        privacy_request_id: privacyRequestId,
        redactions: [...preserved, ...added],
      });
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      }
    },
    [data, privacyRequestId, updateRedactions, message],
  );

  const handleDownload = useCallback(async () => {
    const result = await downloadPackage(privacyRequestId);
    if (result.isError) {
      message.error(
        getErrorMessage(
          result.error,
          "A problem occurred while downloading the access package.",
        ),
      );
      return;
    }
    const blob = result.data;
    if (!(blob instanceof Blob) || blob.size === 0) {
      message.error(
        "The server did not return a ZIP file. The access package may not be ready yet.",
      );
      return;
    }
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `access-package-${privacyRequestId}.zip`;
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }, [downloadPackage, privacyRequestId, message]);

  const handleApprove = useCallback(async () => {
    const result = await approve(privacyRequestId);
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
      return;
    }
    message.success("Access package approved. Upload will continue.");
  }, [approve, privacyRequestId, message]);

  if (isLoading) {
    return <Skeleton active />;
  }

  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        title="Could not load access package"
        description={getErrorMessage(error)}
      />
    );
  }

  if (!data) {
    return <Empty description="No access package available" />;
  }

  const attachments = data.attachments as Array<{
    file_name?: string;
    size?: number;
    content_type?: string;
  }>;

  const isEmpty =
    data.data_uses.length === 0 &&
    !data.other &&
    (!attachments || attachments.length === 0);

  return (
    <Flex vertical gap="large" data-testid="access-package-tab">
      {!isAwaitingReview && (
        <Alert
          type="info"
          showIcon
          title="This request is not currently awaiting access review."
          description="Redactions and approval are only available while the request is in awaiting_access_review."
        />
      )}

      <Flex justify="end">
        <Space>
          <Button
            onClick={handleDownload}
            loading={isDownloading}
            data-testid="download-access-package-btn"
          >
            Download preview
          </Button>
          <Button
            type="primary"
            onClick={handleApprove}
            disabled={!isAwaitingReview}
            loading={isApproving}
            data-testid="approve-access-package-btn"
          >
            Approve & continue
          </Button>
        </Space>
      </Flex>
      <Card size="small">
        <Flex gap="medium" align="center" className="px-4">
          <Statistic title="Fields" value={totalFields} />
          <Divider orientation="vertical" />
          <Statistic title="Systems" value={systemCount} />
          <Divider orientation="vertical" />
          <Statistic title="Redacted" value={redactedCount} />
          {isSaving && (
            <Typography.Text type="secondary">Saving…</Typography.Text>
          )}
        </Flex>
      </Card>

      {isEmpty && <Empty description="Access package is empty" />}

      {data.data_uses.length > 0 && (
        <Collapse
          defaultActiveKey={data.data_uses.map((du) => du.fides_key)}
          items={data.data_uses.map((du) => ({
            key: du.fides_key,
            label: (
              <Space>
                <strong>{du.name}</strong>
                <Typography.Text type="secondary">
                  ({du.categories.reduce((n, c) => n + c.entries.length, 0)}{" "}
                  fields)
                </Typography.Text>
              </Space>
            ),
            children: (
              <Flex vertical gap="large">
                {du.description && (
                  <Typography.Paragraph type="secondary">
                    {du.description}
                  </Typography.Paragraph>
                )}
                {du.categories.map((cat) => (
                  <div key={cat.fides_key}>
                    <Typography.Title level={5} className="mb-2">
                      {cat.name}
                    </Typography.Title>
                    <CategoryTable
                      category={cat}
                      onSelectionChange={handleCategorySelectionChange}
                      disabled={!isAwaitingReview}
                    />
                  </div>
                ))}
              </Flex>
            ),
          }))}
        />
      )}

      {data.other && data.other.categories.length > 0 && (
        <Collapse
          items={[
            {
              key: "other",
              label: <strong>{data.other.name}</strong>,
              children: (
                <Flex vertical gap="large">
                  {data.other.description && (
                    <Typography.Paragraph type="secondary">
                      {data.other.description}
                    </Typography.Paragraph>
                  )}
                  {data.other.categories.map((cat) => (
                    <div key={cat.fides_key}>
                      <Typography.Title level={5} className="mb-2">
                        {cat.name}
                      </Typography.Title>
                      <CategoryTable
                        category={cat}
                        onSelectionChange={handleCategorySelectionChange}
                        disabled={!isAwaitingReview}
                      />
                    </div>
                  ))}
                </Flex>
              ),
            },
          ]}
        />
      )}

      {attachments && attachments.length > 0 && (
        <div>
          <Typography.Title level={5}>Attachments</Typography.Title>
          <List
            size="small"
            bordered
            dataSource={attachments}
            renderItem={(a) => (
              <List.Item>
                <Typography.Text>
                  {a.file_name || "(unnamed attachment)"}
                </Typography.Text>
                {typeof a.size === "number" && (
                  <Typography.Text type="secondary">
                    {a.size} bytes
                  </Typography.Text>
                )}
              </List.Item>
            )}
          />
        </div>
      )}
    </Flex>
  );
};

export default PrivacyRequestDetailsAccessPackageTab;
