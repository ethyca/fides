import {
  Alert,
  Button,
  Flex,
  Radio,
  RadioChangeEvent,
  Result,
  Spin,
  Switch,
  Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import TraversalCanvas from "./TraversalCanvas";
import { LayoutDirection } from "./layout-utils";
import { useGetTraversalPreviewQuery } from "./traversal-preview.slice";
import { ActionType } from "./types";

interface Props {
  propertyId: string;
  actionType: ActionType;
}

const TraversalVisualizerPage = ({ propertyId, actionType }: Props) => {
  const router = useRouter();
  const onActionTypeChange = (next: ActionType) => {
    if (next === actionType) {
      return;
    }
    router.replace(
      `/privacy-requests/visualizer/${encodeURIComponent(propertyId)}/${next}`,
    );
  };
  const [direction, setDirection] = useState<LayoutDirection>("TB");
  const [showUnreachable, setShowUnreachable] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);

  // Always fetch the full payload so we can compute the unreachable count
  // locally and toggle visibility without round-tripping the server.
  const { data, isLoading, isError, refetch } = useGetTraversalPreviewQuery({
    propertyId,
    actionType,
    includeUnreachable: true,
    // Bumping refresh on Regenerate changes the RTK Query cache key, forcing
    // a backend recompute (the request param ``refresh=true`` is also sent).
    refresh: refreshTick > 0,
  });
  const regenerate = () => {
    setRefreshTick((t) => t + 1);
    refetch();
  };

  const unreachableCount =
    data?.integrations.filter((i) => i.reachability === "unreachable").length ??
    0;
  const filteredData =
    data && !showUnreachable
      ? (() => {
          const kept = data.integrations.filter(
            (i) => i.reachability !== "unreachable",
          );
          const keptIds = new Set<string>([
            data.identity_root.id,
            ...kept.map((i) => i.id),
            ...data.manual_tasks.map((m) => m.id),
          ]);
          return {
            ...data,
            integrations: kept,
            edges: data.edges.filter(
              (e) => keptIds.has(e.source) && keptIds.has(e.target),
            ),
          };
        })()
      : data;

  if (isLoading) {
    return <Spin />;
  }
  if (isError) {
    return (
      <Result
        status="error"
        title="Could not load traversal"
        extra={<Button onClick={() => refetch()}>Retry</Button>}
      />
    );
  }

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between" align="center">
        <Typography.Title level={3}>
          Traversal preview · {actionType}
        </Typography.Title>
        <Flex gap="small" align="center">
          {unreachableCount > 0 && (
            <Flex gap={6} align="center">
              <Switch
                size="small"
                checked={showUnreachable}
                onChange={setShowUnreachable}
              />
              <Typography.Text style={{ fontSize: 13 }}>
                Show {unreachableCount} unreachable
              </Typography.Text>
            </Flex>
          )}
          <Radio.Group
            value={actionType}
            onChange={(e: RadioChangeEvent) =>
              onActionTypeChange(e.target.value as ActionType)
            }
            size="small"
          >
            <Radio.Button value="access">Access</Radio.Button>
            <Radio.Button value="erasure">Erasure</Radio.Button>
          </Radio.Group>
          <Radio.Group
            value={direction}
            onChange={(e: RadioChangeEvent) =>
              setDirection(e.target.value as LayoutDirection)
            }
            size="small"
          >
            <Radio.Button value="LR">Horizontal</Radio.Button>
            <Radio.Button value="TB">Vertical</Radio.Button>
          </Radio.Group>
          <Button onClick={regenerate}>Regenerate</Button>
        </Flex>
      </Flex>
      {data?.warnings.length ? (
        <Alert type="warning" message={data.warnings.join(" • ")} closable />
      ) : null}
      <TraversalCanvas payload={filteredData} direction={direction} />
    </Flex>
  );
};

export default TraversalVisualizerPage;
