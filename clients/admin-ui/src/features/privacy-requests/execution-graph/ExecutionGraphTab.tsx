import { Flex, Segmented, Space, Tag, Typography } from "fidesui";
import { useEffect, useMemo, useRef, useState } from "react";

import { PrivacyRequestStatus } from "~/types/api";

import { useGetExecutionGraphQuery } from "../privacy-requests.slice";
import { ExecutionGraphNodeStatus } from "../types";
import { isInternalNode } from "./execution-graph.constants";
import ExecutionGraphView from "./ExecutionGraphView";

const ACTION_TYPE_OPTIONS = [
  { label: "Access", value: "access" },
  { label: "Erasure", value: "erasure" },
  { label: "Consent", value: "consent" },
];

const STATUS_TAG_COLORS: Record<ExecutionGraphNodeStatus, string> = {
  queued: "default",
  executing: "processing",
  complete: "success",
  error: "error",
  skipped: "warning",
  retrying: "warning",
  paused: "default",
  polling: "warning",
};

const TERMINAL_STATES = [
  PrivacyRequestStatus.COMPLETE,
  PrivacyRequestStatus.CANCELED,
  PrivacyRequestStatus.DENIED,
  PrivacyRequestStatus.ERROR,
];

interface ExecutionGraphTabProps {
  privacyRequestId: string;
  privacyRequestStatus: PrivacyRequestStatus;
}

const ExecutionGraphTab = ({
  privacyRequestId,
  privacyRequestStatus,
}: ExecutionGraphTabProps) => {
  const [actionType, setActionType] = useState<string>("access");
  const isTerminal = TERMINAL_STATES.includes(privacyRequestStatus);

  const { data, isLoading, refetch } = useGetExecutionGraphQuery(
    { privacy_request_id: privacyRequestId, action_type: actionType },
    { pollingInterval: isTerminal ? 0 : 2000 },
  );

  const prevIsTerminal = useRef(isTerminal);
  useEffect(() => {
    if (isTerminal && !prevIsTerminal.current) {
      refetch();
    }
    prevIsTerminal.current = isTerminal;
  }, [isTerminal, refetch]);

  const statusCounts = useMemo(() => {
    if (!data?.nodes) {
      return {};
    }
    const counts: Partial<Record<ExecutionGraphNodeStatus, number>> = {};
    data.nodes
      .filter((n) => !isInternalNode(n.collection_address))
      .forEach((n) => {
        counts[n.status] = (counts[n.status] || 0) + 1;
      });
    return counts;
  }, [data?.nodes]);

  const visibleNodeCount = data?.nodes
    ? data.nodes.filter((n) => !isInternalNode(n.collection_address)).length
    : 0;

  const workerStatus = useMemo(() => {
    if (!data?.nodes) {
      return null;
    }
    const visible = data.nodes.filter(
      (n) => !isInternalNode(n.collection_address),
    );
    const executing = visible.find((n) => n.status === "executing");
    if (executing) {
      return `Currently executing: ${executing.collection_address}`;
    }
    const hasQueued = visible.some((n) => n.status === "queued");
    if (!hasQueued) {
      return null;
    }
    const hasCompleted = visible.some((n) => n.status === "complete");
    if (hasCompleted) {
      return "Waiting for next task to start...";
    }
    return "Queued \u2014 waiting for worker";
  }, [data?.nodes]);

  return (
    <Flex vertical gap={16}>
      <Flex justify="space-between" align="center" wrap="wrap" gap={8}>
        <Space size="small">
          <Segmented
            options={ACTION_TYPE_OPTIONS}
            value={actionType}
            onChange={(val) => setActionType(val as string)}
          />
        </Space>

        <Space size="small" wrap>
          {Object.entries(statusCounts).map(([status, count]) => (
            <Tag
              key={status}
              color={STATUS_TAG_COLORS[status as ExecutionGraphNodeStatus]}
            >
              {status}: {count}
            </Tag>
          ))}
        </Space>
      </Flex>

      {!isTerminal && !isLoading && visibleNodeCount > 0 && workerStatus && (
        <Typography.Text
          type="secondary"
          style={{ fontSize: 12, fontStyle: "italic" }}
        >
          {workerStatus}
        </Typography.Text>
      )}

      {isLoading && (
        <Typography.Text type="secondary">Loading graph...</Typography.Text>
      )}

      {!isLoading && visibleNodeCount === 0 && (
        <Typography.Text type="secondary">
          No execution tasks found for this action type.
        </Typography.Text>
      )}

      {data && visibleNodeCount > 0 && (
        <div style={{ height: 500, width: "100%" }}>
          <ExecutionGraphView graphNodes={data.nodes} />
        </div>
      )}
    </Flex>
  );
};

export default ExecutionGraphTab;
