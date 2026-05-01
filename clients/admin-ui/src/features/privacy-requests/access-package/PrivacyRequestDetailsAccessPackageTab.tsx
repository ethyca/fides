import {
  Alert,
  Button,
  Card,
  Collapse,
  Divider,
  Empty,
  Flex,
  Icons,
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
import { PrivacyRequestStatus, RedactionType } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { PrivacyRequestEntity } from "../types";
import {
  useApproveAccessPackageMutation,
  useGetAccessPackageQuery,
  useLazyDownloadAccessPackageQuery,
  useUpdateAccessPackageRedactionsMutation,
} from "./access-package.slice";
import { AccessPackageCategory, AccessPackageEntry } from "./types";
// This UI only manages REDACT-type redactions. REMOVE_FIELD and REMOVE_RECORD
// are passed through unchanged so we don't wipe them, but the checkbox can't
// represent or clear them; if the API starts emitting those, add a per-row
// type picker.
import {
  entryToRedaction,
  redactionKey,
  renderValue,
  rowKeyFor,
} from "./utils";

type Props = {
  subjectRequest: PrivacyRequestEntity;
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
        const k = redactionKey(r.source, r.record_index, r.field_path);
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
    // Defer the revoke so Safari has time to start the download before the
    // URL is invalidated; revoking synchronously after .click() can cancel
    // the download in Safari.
    setTimeout(() => window.URL.revokeObjectURL(url), 0);
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

  const { attachments } = data;

  const isEmpty =
    data.data_uses.length === 0 && !data.other && attachments.length === 0;

  const renderSectionBody = (
    description: string | null | undefined,
    categories: AccessPackageCategory[],
  ) => (
    <Flex vertical gap="large">
      {description && (
        <Typography.Paragraph>{description}</Typography.Paragraph>
      )}
      {categories.map((cat) => (
        <div key={cat.fides_key}>
          <Typography.Title level={3} className="pb-2">
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
  );

  const renderSectionLabel = (
    name: string,
    categories: AccessPackageCategory[],
  ) => (
    <Space>
      <Typography.Text strong>{name}</Typography.Text>
      <Typography.Text type="secondary">
        ({categories.reduce((n, c) => n + c.entries.length, 0)} fields)
      </Typography.Text>
    </Space>
  );

  const sections = [
    ...data.data_uses.map((du) => ({
      key: du.fides_key,
      label: renderSectionLabel(du.name, du.categories),
      children: renderSectionBody(du.description, du.categories),
    })),
    ...(data.other && data.other.categories.length > 0
      ? [
          {
            key: "other",
            label: renderSectionLabel(data.other.name, data.other.categories),
            children: renderSectionBody(
              data.other.description,
              data.other.categories,
            ),
          },
        ]
      : []),
  ];

  const allSectionKeys = sections.map((s) => s.key);

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

      <Flex justify="space-between" align="center" gap="middle">
        <Alert
          type="info"
          showIcon
          title="Uncheck any field to redact it from the access package"
        />
        <Space>
          <Button
            icon={<Icons.Download />}
            onClick={handleDownload}
            loading={isDownloading}
            data-testid="download-access-package-btn"
          >
            Preview
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
          <Divider vertical />
          <Statistic title="Systems" value={systemCount} />
          <Divider vertical />
          <Statistic title="Redacted" value={redactedCount} />
          {isSaving && (
            <Typography.Text type="secondary">Saving…</Typography.Text>
          )}
        </Flex>
      </Card>

      {isEmpty && <Empty description="Access package is empty" />}

      {sections.length > 0 && (
        <Collapse defaultActiveKey={allSectionKeys} items={sections} />
      )}

      {attachments.length > 0 && (
        <div>
          <Typography.Title level={5}>Attachments</Typography.Title>
          <List
            size="small"
            bordered
            dataSource={attachments}
            renderItem={(a) => (
              <List.Item>
                <Typography.Text>{a.file_name}</Typography.Text>
                {typeof a.retrieved_attachment_size === "number" && (
                  <Typography.Text type="secondary">
                    {a.retrieved_attachment_size} bytes
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
