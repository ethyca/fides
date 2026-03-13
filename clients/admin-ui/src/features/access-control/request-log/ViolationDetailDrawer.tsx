import {
  Avatar,
  Button,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Icons,
  Result,
  Spin,
  Tag,
  Typography,
} from "fidesui";
import { useMemo } from "react";

import { Editor } from "~/features/common/yaml/helpers";

import { useGetViolationDetailQuery } from "../access-control.slice";

const { Text, Title } = Typography;

interface ViolationDetailDrawerProps {
  violationId: string | null;
  open: boolean;
  onClose: () => void;
}

export const ViolationDetailDrawer = ({
  violationId,
  open,
  onClose,
}: ViolationDetailDrawerProps) => {
  const {
    data: violation,
    isLoading,
    error,
  } = useGetViolationDetailQuery(violationId!, {
    skip: !violationId,
  });

  const timestamp = violation ? new Date(violation.timestamp) : null;

  const editorHeight = useMemo(() => {
    if (!violation) {
      return 80;
    }
    const lineCount = violation.sql_statement.split("\n").length;
    return Math.max(80, lineCount * 18 + 42);
  }, [violation]);

  return (
    <Drawer
      title="Violation details"
      placement="right"
      onClose={onClose}
      open={open}
      width={480}
      footer={
        <Flex gap="small" justify="flex-end">
          <Button>Edit policy</Button>
          <Button type="primary">Create new policy</Button>
        </Flex>
      }
    >
      {isLoading && (
        <Flex justify="center" align="center" className="py-16">
          <Spin />
        </Flex>
      )}
      {error && (
        <Result
          status="error"
          title="Failed to load violation details"
          subTitle="Please try again later."
        />
      )}
      {violation && timestamp && (
        <div className="space-y-6">
          <div>
            <Text className="mb-2 block text-xs font-semibold text-neutral-10">
              Violation reason
            </Text>
            <div className="rounded-lg bg-gray-50 p-5">
              <Text className="text-sm leading-relaxed">
                {violation.ai_reason ?? "Analysis pending..."}
              </Text>
            </div>
          </div>

          <div>
            <Text className="mb-2 block text-xs font-semibold text-neutral-10">
              Data consumer
            </Text>
            <Flex justify="space-between" align="center">
              <Flex align="center" gap="middle">
                <div>
                  <Text strong className="block">
                    {violation.consumer}
                  </Text>
                  <a
                    href={`mailto:${violation.consumer_email}`}
                    className="text-sm text-neutral-10/60 hover:underline"
                  >
                    {violation.consumer_email}
                  </a>
                </div>
              </Flex>
            </Flex>
          </div>

          <div>
            <Text className="mb-2 block text-xs font-semibold text-neutral-10">
              Details
            </Text>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-gray-50 px-4 py-3">
                <Text className="mb-1 block text-xs text-neutral-10">
                  Timestamp
                </Text>
                <Text className="text-sm">
                  {timestamp.toISOString().slice(0, 10)}{" "}
                  {timestamp.toISOString().slice(11, 19)}
                </Text>
              </div>
              <div className="rounded-lg bg-gray-50 px-4 py-3">
                <Text className="mb-1 block text-xs text-neutral-10">
                  Data use
                </Text>
                <Text className="text-sm">{violation.data_use}</Text>
              </div>
              <div className="rounded-lg bg-gray-50 px-4 py-3">
                <Text className="mb-1 block text-xs text-neutral-10">
                  Dataset
                </Text>
                <Text className="text-sm">{violation.dataset}</Text>
              </div>
              <div className="rounded-lg bg-gray-50 px-4 py-3">
                <Text className="mb-1 block text-xs text-neutral-10">
                  Policy
                </Text>
                <Text className="text-sm">{violation.policy}</Text>
              </div>
            </div>
          </div>

          <div>
            <Text className="mb-2 block text-xs font-semibold text-neutral-10">
              Request context
            </Text>
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <Editor
                defaultLanguage="sql"
                value={violation.sql_statement}
                height={editorHeight}
                theme="light"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  lineNumbers: "off",
                  scrollBeyondLastLine: false,
                  folding: false,
                  fontSize: 12,
                  fontFamily: "Menlo, monospace",
                  wordWrap: "on",
                  padding: { top: 12, bottom: 12 },
                  renderLineHighlight: "none",
                  overviewRulerLanes: 0,
                  scrollbar: {
                    vertical: "hidden",
                    horizontal: "hidden",
                  },
                }}
              />
            </div>
          </div>

          <div>
            <Text className="mb-2 block text-xs font-semibold text-neutral-10">
              Policy deviated
            </Text>
            <div className="rounded-lg border border-gray-200 p-5">
              <Flex align="center" gap="small" className="mb-2">
                <Title level={5} className="!m-0">
                  {violation.policy}
                </Title>
                <Tag color={CUSTOM_TAG_COLOR.SANDSTONE}>
                  {violation.data_use}
                </Tag>
              </Flex>
              <Text type="secondary" className="block text-sm leading-relaxed">
                {violation.policy_description}
              </Text>
              <Flex align="center" gap={4} className="mt-3">
                <Text type="secondary" className="text-sm font-medium">
                  View policy
                </Text>
                <Icons.ArrowRight size={14} />
              </Flex>
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
};
