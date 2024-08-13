import { DataFlowAccordion } from "common/system-data-flow/DataFlowAccordion";
import { Box, Link, Text, useToast } from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { type TabData } from "~/features/common/DataTabs";
import { useFeatures, useFlags } from "~/features/common/features";
import {
  DirtyFormConfirmationModal,
  useIsAnyFormDirty,
} from "~/features/common/hooks/useIsAnyFormDirty";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import ToastLink from "~/features/common/ToastLink";
import ConnectionForm from "~/features/datastore-connections/system_portal_config/ConnectionForm";
import { ConsentAutomationForm } from "~/features/datastore-connections/system_portal_config/ConsentAutomationForm";
import {
  setLockedForGVL,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import SystemHistoryTable from "~/features/system/history/SystemHistoryTable";
import PrivacyDeclarationStep from "~/features/system/privacy-declarations/PrivacyDeclarationStep";
import {
  selectActiveSystem,
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system/system.slice";
import SystemInformationForm from "~/features/system/SystemInformationForm";
import { SystemResponse } from "~/types/api";

// The toast doesn't seem to handle next links well, so use buttons with onClick
// handlers instead
const ToastMessage = ({
  onViewDatamap,
  onAddPrivacyDeclaration,
}: {
  onViewDatamap: () => void;
  onAddPrivacyDeclaration: () => void;
}) => (
  <Box>
    <Text fontWeight="700">System has been saved successfully</Text>
    <Text textColor="gray.700" whiteSpace="inherit">
      Your system has been added to your data map. You can{" "}
      <ToastLink onClick={onViewDatamap}>view it now</ToastLink> and come back
      to finish this setup when you’re ready. Or you can progress to{" "}
      <ToastLink onClick={onAddPrivacyDeclaration}>
        adding your privacy declarations in the next tab
      </ToastLink>
      .
    </Text>
  </Box>
);

const useSystemFormTabs = ({
  isCreate,
  initialTabIndex,
}: {
  initialTabIndex?: number;
  /** If true, then some editing features will not be enabled */
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
  const {
    flags: { dataDiscoveryAndDetection },
  } = useFlags();
  const { plus: hasPlus } = useFeatures();

  // Once we have saved the system basics, subscribe to the query so that activeSystem
  // stays up to date when redux invalidates the cache (for example, when we patch a connection config)
  const { data: systemFromApi } = useGetSystemByFidesKeyQuery(
    activeSystem?.fides_key,
    { skip: !activeSystem },
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
    [activeSystem, dispatch, router, systemOrDatamapRoute, toast],
  );

  useEffect(() => {
    /**
     * The first time this component mounts, if it's a create, make sure we don't have an active system
     * This can happen if the user was editing a system, then navigated away by typing in a new URL path
     * When navigating not through a URL path, the return unmount should handle resetting the system
     */
    if (isCreate) {
      dispatch(setActiveSystem(undefined));
      dispatch(setSuggestions("initial"));
      dispatch(setLockedForGVL(false));
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
    [attemptAction],
  );

  const showNewIntegrationNotice = hasPlus && dataDiscoveryAndDetection;

  const tabData: TabData[] = [
    {
      label: "Information",
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
                <Link
                  as={NextLink}
                  href={systemOrDatamapRoute}
                  textDecor="underline"
                >
                  ready to view in your data map
                </Link>
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
            <Text fontSize="sm" lineHeight={5}>
              {showNewIntegrationNotice ? (
                <>
                  Add an integration to start managing privacy requests and
                  consent. Visit{" "}
                  <Link href={INTEGRATION_MANAGEMENT_ROUTE} color="purple.500">
                    Integration Management
                  </Link>{" "}
                  to set up monitoring on databases.
                </>
              ) : (
                "Integrations are used to process privacy requests for access erasure, portability, rectification, and consent."
              )}
            </Text>
          </Box>
          <ConnectionForm
            connectionConfig={activeSystem.connection_configs}
            systemFidesKey={activeSystem.fides_key}
          />
          {activeSystem.connection_configs?.key && (
            <ConsentAutomationForm
              m={6}
              connectionKey={activeSystem.connection_configs?.key}
            />
          )}
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

  return { tabData, tabIndex, onTabChange };
};
export default useSystemFormTabs;
