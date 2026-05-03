import { Flex, Spin } from "fidesui";
import { useRouter } from "next/router";
import { ReactNode, useState } from "react";

import CanvasHeader from "./header/CanvasHeader";
import { useGetTraversalPreviewQuery } from "./traversal-preview.slice";
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

  let canvasContent: ReactNode;
  if (!propertyKey) {
    canvasContent = (
      <Flex
        align="center"
        justify="center"
        style={{ height: "calc(100vh - 240px)" }}
      >
        <span style={{ color: "var(--fidesui-color-text-tertiary)" }}>
          Select a property to preview its DSR traversal.
        </span>
      </Flex>
    );
  } else if (isLoading) {
    canvasContent = (
      <Flex
        align="center"
        justify="center"
        style={{ height: "calc(100vh - 240px)" }}
      >
        <Spin />
      </Flex>
    );
  } else {
    canvasContent = <TraversalCanvas payload={filteredPayload} />;
  }

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
      {canvasContent}
    </>
  );
};

export default TraversalVisualizerPage;
