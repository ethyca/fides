import { Box, Center, Flex, Spinner } from "@fidesui/react";
import dynamic from "next/dynamic";
import { useCallback, useContext, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useIsAnyFormDirty } from "~/features/common/hooks/useIsAnyFormDirty";
import DatamapDrawer from "~/features/datamap/datamap-drawer/DatamapDrawer";
import { DatamapGraphContext } from "~/features/datamap/datamap-graph/DatamapGraphContext";
import { useTableInstance } from "~/features/datamap/datamap-table/hooks/";
import SettingsBar from "~/features/datamap/SettingsBar";

import { selectIsGettingStarted, selectIsMapOpen } from "./datamap.slice";
import DatamapTable from "./datamap-table/DatamapTable";
import GetStarted from "./GetStarted";

const SpatialDatamap = dynamic(
  () => import("~/features/datamap/SpatialDatamap"),
  { ssr: false }
);

const useHome = () => {
  const isMapOpen = useAppSelector(selectIsMapOpen);
  const isGettingStarted = useAppSelector(selectIsGettingStarted);
  const datamapGraphRef = useContext(DatamapGraphContext);

  const { attemptAction } = useIsAnyFormDirty();
  const [selectedSystemId, setSelectedSystemIdInner] = useState<
    string | undefined
  >();

  const setSelectedSystemId = useCallback(
    (systemId: string) => {
      attemptAction().then((modalConfirmed: boolean) => {
        if (modalConfirmed) {
          setSelectedSystemIdInner(systemId);
        }
      });
    },
    [attemptAction, setSelectedSystemIdInner]
  );

  const resetSelectedSystemId = useCallback(() => {
    attemptAction().then((modalConfirmed: boolean) => {
      if (modalConfirmed && selectedSystemId) {
        if (datamapGraphRef.current) {
          datamapGraphRef.current?.$id(selectedSystemId).unselect();
        }
        setSelectedSystemIdInner(undefined);
      }
    });
  }, [attemptAction, datamapGraphRef, selectedSystemId]);

  return {
    isMapOpen,
    isGettingStarted,
    selectedSystemId,
    setSelectedSystemId,
    resetSelectedSystemId,
  };
};

const Datamap = () => {
  const {
    isMapOpen,
    isGettingStarted,
    setSelectedSystemId,
    selectedSystemId,
    resetSelectedSystemId,
  } = useHome();
  const { isLoading } = useTableInstance();
  if (isLoading) {
    return (
      <Center width="100%" flex="1">
        <Spinner />
      </Center>
    );
  }

  if (isGettingStarted) {
    return <GetStarted />;
  }

  return (
    <Flex direction="column" height="100%">
      <Box marginBottom={3} marginRight={10}>
        <SettingsBar />
      </Box>
      <Flex
        position="relative"
        flex={1}
        direction="row"
        overflow="auto"
        borderWidth="1px"
        borderStyle="solid"
        borderColor="gray.200"
      >
        {isMapOpen ? (
          <Box flex={1} minWidth="50%" maxWidth="100%">
            <SpatialDatamap setSelectedSystemId={setSelectedSystemId} />
          </Box>
        ) : null}
        {!isMapOpen ? (
          <Box flex={1} minWidth="50%" maxWidth="100%">
            <DatamapTable setSelectedSystemId={setSelectedSystemId} />
          </Box>
        ) : null}
        <DatamapDrawer
          selectedSystemId={selectedSystemId}
          resetSelectedSystemId={resetSelectedSystemId}
        />
      </Flex>
    </Flex>
  );
};

export default Datamap;
