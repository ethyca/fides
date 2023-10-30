import { Box, Button, Text, useToast } from "@fidesui/react";
import { DataFlowAccordion } from "common/system-data-flow/DataFlowAccordion";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";
import { useFeatures } from "~/features/common/features";
import {
  DirtyFormConfirmationModal,
  useIsAnyFormDirty,
} from "~/features/common/hooks/useIsAnyFormDirty";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import ConnectionForm from "~/features/datastore-connections/system_portal_config/ConnectionForm";
import PrivacyDeclarationStep from "~/features/system/privacy-declarations/PrivacyDeclarationStep";
import { SystemResponse } from "~/types/api";

import SystemHistoryTable from "./history/SystemHistoryTable";
import {
  selectActiveSystem,
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "./system.slice";
import SystemInformationForm from "./SystemInformationForm";

// The toast doesn't seem to handle next links well, so use buttons with onClick
// handlers instead
const ToastMessage = ({
  onViewDatamap,
  onAddPrivacyDeclaration,
}: {
  onViewDatamap: () => void;
  onAddPrivacyDeclaration: () => void;
}) => {
  const linkButtonProps = {
    variant: "link",
    textDecor: "underline",
    textColor: "gray.700",
    fontWeight: "medium",
    // allow lines to wrap
    display: "initial",
    cursor: "pointer",
  };
  return (
    <Box>
      <Text fontWeight="700">System has been saved successfully</Text>
      <Text textColor="gray.700" whiteSpace="inherit">
        Your system has been added to your data map. You can{" "}
        <Button
          as="a"
          onClick={onViewDatamap}
          {...linkButtonProps}
          // typescript doesn't like passing whiteSpace via linkButtonProps
          whiteSpace="inherit"
        >
          view it now
        </Button>{" "}
        and come back to finish this setup when you’re ready. Or you can
        progress to{" "}
        <Button
          as="a"
          onClick={onAddPrivacyDeclaration}
          {...linkButtonProps}
          whiteSpace="inherit"
        >
          adding your privacy declarations in the next tab
        </Button>
        .
      </Text>
    </Box>
  );
};

const SystemFormTabs = ({
  initialTabIndex = 0,
  isCreate,
}: {
  /** If true, then some editing features will not be enabled */
  initialTabIndex?: number;
  isCreate?: boolean;
}) => {
  const [tabIndex, setTabIndex] = useState(initialTabIndex);
  const [showSaveMessage, setShowSaveMessage] = useState(false);
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const activeSystem = useAppSelector(selectActiveSystem) as SystemResponse;
  const [systemProcessesPersonalData, setSystemProcessesPersonalData] =
    useState<boolean | undefined>(undefined);
  const { plus: isPlusEnabled } = useFeatures();

  // Once we have saved the system basics, subscribe to the query so that activeSystem
  // stays up to date when redux invalidates the cache (for example, when we patch a connection config)
  const { data: systemFromApi } = useGetSystemByFidesKeyQuery(
    activeSystem?.fides_key,
    { skip: !activeSystem }
  );

  useEffect(() => {
    dispatch(setActiveSystem(systemFromApi));
  }, [systemFromApi, dispatch]);

  useEffect(() => {
    if (activeSystem) {
      setSystemProcessesPersonalData(activeSystem.processes_personal_data);
    }
  }, [activeSystem]);

  const handleSuccess = useCallback(
    (system: SystemResponse) => {
      // show a save message if this is the first time the system was saved
      if (activeSystem === undefined) {
        setShowSaveMessage(true);
      }
      dispatch(setActiveSystem(system));
      const toastParams = {
        ...DEFAULT_TOAST_PARAMS,
        description: (
          <ToastMessage
            onViewDatamap={() => {
              router.push(systemOrDatamapRoute).then(() => {
                toast.closeAll();
              });
            }}
            onAddPrivacyDeclaration={() => {
              setTabIndex(1);
              toast.closeAll();
            }}
          />
        ),
      };
      toast({ ...toastParams });
    },
    [activeSystem, dispatch, router, systemOrDatamapRoute, toast]
  );

  useEffect(() => {
    /**
     * The first time this component mounts, if it's a create, make sure we don't have an active system
     * This can happen if the user was editing a system, then navigated away by typing in a new URL path
     * When navigating not through a URL path, the return unmount should handle resetting the system
     */
    if (isCreate) {
      dispatch(setActiveSystem(undefined));
    }
    return () => {
      // on unmount, unset the active system
      dispatch(setActiveSystem(undefined));
    };
  }, [dispatch, isCreate]);

  const { attemptAction } = useIsAnyFormDirty();

  const onTabChange = useCallback(
    (index: number) => {
      attemptAction().then((modalConfirmed: boolean) => {
        if (modalConfirmed) {
          setTabIndex(index);
        }
      });
    },
    [attemptAction]
  );

  const tabData: TabData[] = [
    {
      label: "System information",
      content: (
        <>
          <Box px={6} mb={9}>
            <DirtyFormConfirmationModal />
            <SystemInformationForm
              onSuccess={handleSuccess}
              system={activeSystem}
            />
          </Box>
          {showSaveMessage ? (
            <Box backgroundColor="gray.100" px={6} py={3}>
              <Text
                color="gray.500"
                fontSize="sm"
                data-testid="save-help-message"
              >
                Now that you have saved this new system it is{" "}
                <NextLink href={systemOrDatamapRoute} passHref>
                  <Text as="a" textDecor="underline">
                    ready to view in your data map
                  </Text>
                </NextLink>
                . You can return to this setup at any time to add privacy
                declarations to this system.
              </Text>
            </Box>
          ) : null}
        </>
      ),
    },
    {
      label: "Data uses",
      content: activeSystem ? (
        <Box px={6} width={{ base: "100%", lg: "70%" }}>
          <PrivacyDeclarationStep system={activeSystem} />
        </Box>
      ) : null,
      isDisabled: !activeSystem || !systemProcessesPersonalData,
    },
    {
      label: "Data flow",
      content: activeSystem ? (
        <Box width={{ base: "100%", lg: "70%" }}>
          <Box px={6} paddingBottom={2}>
            <Text
              fontSize="md"
              lineHeight={6}
              fontWeight="bold"
              marginBottom={3}
            >
              Data flow
            </Text>
            <Text fontSize="sm" lineHeight={5} fontWeight="medium">
              Data flow describes the flow of data between systems in your Data
              Map. Below, you can configure Source and Destination systems and
              the corresponding links will be drawn in the Data Map graph.
              Source systems are systems that send data to this system while
              Destination systems receive data from this system.
            </Text>
          </Box>
          <DataFlowAccordion system={activeSystem} isSystemTab />
        </Box>
      ) : null,
      isDisabled: !activeSystem,
    },
    {
      label: "Integrations",
      content: activeSystem ? (
        <Box width={{ base: "100%", lg: "70%" }}>
          <Box px={6} paddingBottom={2}>
            <Text fontSize="sm" lineHeight={5} fontWeight="medium">
              Integrations are used to process privacy requests for access,
              erasure, portability, rectification, and consent.
            </Text>
          </Box>
          <ConnectionForm
            connectionConfig={activeSystem.connection_configs}
            systemFidesKey={activeSystem.fides_key}
          />
        </Box>
      ) : null,
      isDisabled: !activeSystem,
    },
  ];

  if (isPlusEnabled) {
    tabData.push({
      label: "History",
      content: activeSystem ? (
        <Box width={{ base: "100%", lg: "70%" }}>
          <Box px={6} paddingBottom={6}>
            <Text fontSize="sm" lineHeight={5} fontWeight="medium">
              All changes to this system are tracked here in this audit table by
              date and by user. You can inspect the changes by selecting any of
              the events listed.
            </Text>
          </Box>
          <SystemHistoryTable system={activeSystem} />
        </Box>
      ) : null,
      isDisabled: !activeSystem,
    });
  }

  return (
    <DataTabs
      data={tabData}
      data-testid="system-tabs"
      index={tabIndex}
      isLazy
      isManual
      onChange={onTabChange}
    />
  );
};

export default SystemFormTabs;
