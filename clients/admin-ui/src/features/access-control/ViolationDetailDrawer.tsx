import { format } from "date-fns";
import {
  antTheme,
  Button,
  Card,
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

import { useGetViolationDetailQuery } from "./access-control.slice";

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
  const { token } = antTheme.useToken();
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
    const lineCount = (violation.sql_statement ?? "").split("\n").length;
    return Math.max(80, lineCount * 18 + 42);
  }, [violation]);

  return (
    <Drawer
      title="Violation details"
      placement="right"
      onClose={onClose}
      open={open}
      footer={
        <Flex gap="small" justify="flex-end">
          <Button disabled>Edit policy</Button>
          <Button type="primary" disabled>
            Create new policy
          </Button>
        </Flex>
      }
    >
      {isLoading && <Spin />}
      {error && (
        <Result
          status="error"
          title="Failed to load violation details"
          subTitle="Please try again later."
        />
      )}
      {violation && timestamp && (
        <Flex vertical gap={24}>
          <section>
            <Text type="secondary" strong className="mb-2 block">
              Violation reason
            </Text>
            <Card size="small">
              <Text>{violation.ai_reason ?? "Analysis pending..."}</Text>
            </Card>
          </section>

          <section>
            <Text type="secondary" strong className="mb-2 block">
              Data consumer
            </Text>
            <Flex vertical>
              <Text strong>{violation.consumer}</Text>
              {violation.consumer_email && (
                <a href={`mailto:${violation.consumer_email}`}>
                  <Text type="secondary">{violation.consumer_email}</Text>
                </a>
              )}
            </Flex>
          </section>

          <section>
            <Text type="secondary" strong className="mb-2 block">
              Details
            </Text>
            <div className="grid grid-cols-2 gap-3">
              <Card size="small">
                <Text type="secondary" className="mb-1 block">
                  Timestamp
                </Text>
                <Text>{format(timestamp, "yyyy-MM-dd HH:mm:ss")}</Text>
              </Card>
              <Card size="small">
                <Text type="secondary" className="mb-1 block">
                  Data use
                </Text>
                <Text>{violation.data_use ?? "N/A"}</Text>
              </Card>
              <Card size="small">
                <Text type="secondary" className="mb-1 block">
                  Dataset
                </Text>
                <Text>{violation.dataset}</Text>
              </Card>
              <Card size="small">
                <Text type="secondary" className="mb-1 block">
                  Policy
                </Text>
                <Text>{violation.policy ?? "N/A"}</Text>
              </Card>
            </div>
          </section>

          <section>
            <Text type="secondary" strong className="mb-2 block">
              Request context
            </Text>
            <Card size="small" className="overflow-hidden">
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
                  fontFamily: token.fontFamilyCode,
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
            </Card>
          </section>

          <section>
            <Text type="secondary" strong className="mb-2 block">
              Policy deviated
            </Text>
            {violation.policy ? (
              <Card size="small">
                <Flex align="center" gap="small" className="mb-2">
                  <Title level={5} className="!m-0">
                    {violation.policy}
                  </Title>
                  <Tag color={CUSTOM_TAG_COLOR.SANDSTONE}>
                    {violation.data_use}
                  </Tag>
                </Flex>
                <Text type="secondary">{violation.policy_description}</Text>
                <Flex align="center" gap={4} className="mt-3">
                  <Text type="secondary">View policy</Text>
                  <Icons.ArrowRight size={14} />
                </Flex>
              </Card>
            ) : (
              <Card size="small" className="text-center">
                <Text type="secondary" className="mb-2 block">
                  No policy associated with this violation
                </Text>
                <Button size="small">Add policy</Button>
              </Card>
            )}
          </section>
        </Flex>
      )}
    </Drawer>
  );
};
