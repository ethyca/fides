import {
  Alert,
  Button,
  Flex,
  Radio,
  RadioChangeEvent,
  Result,
  Spin,
  Typography,
} from "fidesui";
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
  const [direction, setDirection] = useState<LayoutDirection>("LR");
  const [refreshTick, setRefreshTick] = useState(0);
  const { data, isLoading, isError, refetch } = useGetTraversalPreviewQuery({
    propertyId,
    actionType,
    // Bumping refresh on Regenerate changes the RTK Query cache key, forcing
    // a backend recompute (the request param ``refresh=true`` is also sent).
    refresh: refreshTick > 0,
  });
  const regenerate = () => {
    setRefreshTick((t) => t + 1);
    refetch();
  };

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
      <TraversalCanvas payload={data} direction={direction} />
    </Flex>
  );
};

export default TraversalVisualizerPage;
