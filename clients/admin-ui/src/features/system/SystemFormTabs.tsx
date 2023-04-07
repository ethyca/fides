import { Box, Button, Text, useToast } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import PrivacyDeclarationStep from "~/features/system/privacy-declarations/PrivacyDeclarationStep";
import { System } from "~/types/api";

import { selectActiveSystem, setActiveSystem } from "./system.slice";
import SystemInformationForm from "./SystemInformationForm";
import UnmountWarning from "./UnmountWarning";
import { DataFlowAccordion } from "common/system-data-flow/DataFlowAccordion";

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
  isCreate,
}: {
  /** If true, then some editing features will not be enabled */
  isCreate?: boolean;
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [queuedIndex, setQueuedIndex] = useState<number | undefined>(undefined);
  const [showSaveMessage, setShowSaveMessage] = useState(false);
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const activeSystem = useAppSelector(selectActiveSystem);

  const handleSuccess = (system: System) => {
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
  };

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

  const checkTabChange = (index: number) => {
    // While privacy declarations aren't updated yet, only apply the "unsaved changes" modal logic
    // to the system information tab
    if (index === 0) {
      setTabIndex(index);
    } else {
      setQueuedIndex(index);
    }
  };

  const continueTabChange = () => {
    if (queuedIndex) {
      setTabIndex(queuedIndex);
      setQueuedIndex(undefined);
    }
  };

  const tabData: TabData[] = [
    {
      label: "System information",
      content: (
        <>
          <Box px={6} mb={9}>
            <SystemInformationForm
              onSuccess={handleSuccess}
              system={activeSystem}
              abridged={isCreate}
            >
              <UnmountWarning
                isUnmounting={queuedIndex !== undefined}
                onContinue={continueTabChange}
                onCancel={() => setQueuedIndex(undefined)}
              />
            </SystemInformationForm>
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
          <PrivacyDeclarationStep system={activeSystem as System} />
        </Box>
      ) : null,
      isDisabled: !activeSystem,
    },
    {
      label: "Data flow",
      content: activeSystem ? (
        <Box px={6} width={{ base: "100%", lg: "70%" }}>
          <Text fontSize="md" lineHeight={6} fontWeight="bold">Data flow</Text>
          <Text fontSize="sm" lineHeight={5} fontWeight="medium">
            Data flow describes the flow of data between systems in your Data
            Map. Below, you can configure Source and Destination systems and the
            corresponding links will be drawn in the Data Map graph. Source
            systems are systems that send data to this system while Destination
            systems receive data from this system.
          </Text>
          <DataFlowAccordion system={activeSystem} />
        </Box>
      ) : null,
      isDisabled: !activeSystem,
    },
  ];

  return (
    <DataTabs
      data={tabData}
      data-testid="system-tabs"
      index={tabIndex}
      isLazy
      isManual
      onChange={checkTabChange}
    />
  );
};

export default SystemFormTabs;
