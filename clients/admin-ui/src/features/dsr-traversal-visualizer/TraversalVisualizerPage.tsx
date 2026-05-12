import { skipToken } from "@reduxjs/toolkit/query";
import { Card, Flex, Spin, Text } from "fidesui";
import { useRouter } from "next/router";
import { ReactNode, useState } from "react";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

import { CanvasHeader } from "./header/CanvasHeader";
import {
  useGetTraversalPreviewQuery,
  useLazyGetTraversalPreviewQuery,
} from "./traversal-preview.slice";
import { TraversalCanvas } from "./TraversalCanvas";
import styles from "./TraversalVisualizerPage.module.scss";
import { ActionType, Reachability } from "./types";

interface Props {
  propertyKey: string | null;
  actionType: ActionType;
}

export const TraversalVisualizerPage = ({ propertyKey, actionType }: Props) => {
  const router = useRouter();
  const [showNotTouched, setShowNotTouched] = useState(true);

  // Prefetch taxonomy data at the page level so data-category labels resolve
  // before first paint of the integration nodes. RTK Query dedupes the
  // identical calls inside IntegrationNode.
  useTaxonomies();
  const { data, isLoading } = useGetTraversalPreviewQuery(
    propertyKey
      ? { propertyId: propertyKey, actionType, includeUnreachable: true }
      : skipToken,
  );
  const [triggerRefresh] = useLazyGetTraversalPreviewQuery();

  const filteredPayload = data
    ? {
        ...data,
        integrations: showNotTouched
          ? data.integrations
          : data.integrations.filter(
              (i) => i.reachability !== Reachability.UNREACHABLE,
            ),
      }
    : undefined;

  const goTo = (key: string, action: ActionType = actionType) => {
    router.replace(`/dsr-traversal/${key}/${action}`);
  };

  let canvasContent: ReactNode;
  if (!propertyKey) {
    canvasContent = (
      <Flex align="center" justify="center" flex={1}>
        <Text type="secondary">
          Select a property to preview its DSR traversal.
        </Text>
      </Flex>
    );
  } else if (isLoading) {
    canvasContent = (
      <Flex align="center" justify="center" flex={1}>
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
        onRegenerate={() =>
          propertyKey &&
          triggerRefresh({
            propertyId: propertyKey,
            actionType,
            includeUnreachable: true,
            refresh: true,
          })
        }
      />
      <Card className={styles.canvasCard}>{canvasContent}</Card>
    </>
  );
};
