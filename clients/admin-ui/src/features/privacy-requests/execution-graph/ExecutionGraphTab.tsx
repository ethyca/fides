import { Breadcrumb, Flex, Segmented, Space, Tag, Typography } from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { PrivacyRequestStatus } from "~/types/api";

import { useGetExecutionGraphQuery } from "../privacy-requests.slice";
import { ExecutionGraphNode, ExecutionGraphNodeStatus } from "../types";
import { isInternalNode } from "./execution-graph.constants";
import ExecutionGraphView from "./ExecutionGraphView";
import { useExecutionGraphNavigation } from "./useExecutionGraphNavigation";

const ACTION_TYPE_OPTIONS = [
  { label: "Access", value: "access" },
  { label: "Erasure", value: "erasure" },
  { label: "Consent", value: "consent" },
];

const STATUS_TAG_COLORS: Record<ExecutionGraphNodeStatus, string> = {
  pending: "default",
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
    { pollingInterval: 2000 },
  );

  const prevIsTerminal = useRef(isTerminal);
  useEffect(() => {
    if (isTerminal && !prevIsTerminal.current) {
      refetch();
    }
    prevIsTerminal.current = isTerminal;
  }, [isTerminal, refetch]);

  const visibleNodes = useMemo(
    () =>
      data?.nodes?.filter((n) => !isInternalNode(n.collection_address)) ?? [],
    [data?.nodes],
  );

  const { viewMode, selectedDataset, selectDataset, goBack } =
    useExecutionGraphNavigation(visibleNodes.length);

  const statusCounts = useMemo(() => {
    const counts: Partial<Record<ExecutionGraphNodeStatus, number>> = {};
    visibleNodes.forEach((n) => {
      counts[n.status] = (counts[n.status] || 0) + 1;
    });
    return counts;
  }, [visibleNodes]);

  const executingNodes = useMemo(
    () =>
      visibleNodes.filter(
        (n) => n.status === "executing" || n.status === "retrying",
      ),
    [visibleNodes],
  );


  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);

  const handleExecutingClick = useCallback(() => {
    if (executingNodes.length > 0) {
      const node = executingNodes[0];
      selectDataset(node.dataset_name);
      setFocusNodeId(null);
      requestAnimationFrame(() => {
        setFocusNodeId(node.collection_address);
      });
    }
  }, [executingNodes, selectDataset]);

  const handleGoBack = useCallback(() => {
    const dataset = selectedDataset;
    goBack();
    setFocusNodeId(null);
    requestAnimationFrame(() => {
      setFocusNodeId(dataset);
    });
  }, [selectedDataset, goBack]);

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

      {viewMode === "collections" && selectedDataset && (
        <Breadcrumb
          items={[
            { title: "All datasets", onClick: handleGoBack, className: "cursor-pointer" },
            { title: selectedDataset },
          ]}
        />
      )}

      {!isLoading && visibleNodes.length > 0 && (
        <Typography.Text
          type="secondary"
          style={{ fontSize: 12, fontStyle: "italic" }}
        >
          {executingNodes.length > 0 ? (
            <>
              Currently executing{" "}
              <Typography.Link
                style={{ fontSize: 12, fontStyle: "italic" }}
                onClick={handleExecutingClick}
              >
                {executingNodes[0].collection_address}
              </Typography.Link>
            </>
          ) : isTerminal ? (
            "No tasks executing for this request"
          ) : (
            "Waiting for worker to pick up next task"
          )}
        </Typography.Text>
      )}

      {isLoading && (
        <Typography.Text type="secondary">Loading graph...</Typography.Text>
      )}

      {!isLoading && visibleNodes.length === 0 && (
        <Typography.Text type="secondary">
          No execution tasks found for this action type.
        </Typography.Text>
      )}

      {data && visibleNodes.length > 0 && (
        <div style={{ height: 500, width: "100%" }}>
          <ExecutionGraphView
            graphNodes={data.nodes}
            viewMode={viewMode}
            selectedDataset={selectedDataset}
            onDatasetClick={selectDataset}
            focusNodeId={focusNodeId}
          />
        </div>
      )}
    </Flex>
  );
};

export default ExecutionGraphTab;
