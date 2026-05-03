import { Flex, Spin } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { useGetTraversalPreviewQuery } from "./traversal-preview.slice";
import CanvasHeader from "./header/CanvasHeader";
import TraversalCanvas from "./TraversalCanvas";

interface Props {
  propertyKey: string | null;
  actionType: "access" | "erasure";
}

const TraversalVisualizerPage = ({ propertyKey, actionType }: Props) => {
  const router = useRouter();
  const [showNotTouched, setShowNotTouched] = useState(true);
  const { data, isLoading, refetch } = useGetTraversalPreviewQuery(
    { propertyId: propertyKey!, actionType, includeUnreachable: true },
    { skip: !propertyKey },
  );

  const filteredPayload = data
    ? {
        ...data,
        integrations: showNotTouched
          ? data.integrations
          : data.integrations.filter((i) => i.reachability !== "unreachable"),
      }
    : undefined;

  const goTo = (key: string, action = actionType) => {
    router.replace(`/dsr-traversal/${key}/${action}`);
  };

  return (
    <>
      <CanvasHeader
        propertyKey={propertyKey}
        actionType={actionType}
        showNotTouched={showNotTouched}
        payload={filteredPayload}
        onPropertyChange={(k) => goTo(k)}
        onActionChange={(a) => propertyKey && goTo(propertyKey, a)}
        onShowNotTouchedChange={setShowNotTouched}
        onRegenerate={() => refetch()}
      />
      {!propertyKey ? (
        <Flex
          align="center"
          justify="center"
          style={{ height: "calc(100vh - 240px)" }}
        >
          <span style={{ color: "var(--fidesui-color-text-tertiary)" }}>
            Select a property to preview its DSR traversal.
          </span>
        </Flex>
      ) : isLoading ? (
        <Flex
          align="center"
          justify="center"
          style={{ height: "calc(100vh - 240px)" }}
        >
          <Spin />
        </Flex>
      ) : (
        <TraversalCanvas payload={filteredPayload} />
      )}
    </>
  );
};

export default TraversalVisualizerPage;
