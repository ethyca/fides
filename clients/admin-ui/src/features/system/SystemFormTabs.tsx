import { Box, useToast } from "@fidesui/react";
import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";
import { System } from "~/types/api";

import { successToastParams } from "../common/toast";
import PrivacyDeclarationStep from "./PrivacyDeclarationStep";
import { selectActiveSystem, setActiveSystem } from "./system.slice";
import SystemInformationForm from "./SystemInformationForm";

const SystemFormTabs = ({
  isCreate,
}: {
  /** If true, then some editing features will not be enabled */
  isCreate?: boolean;
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const router = useRouter();
  const toast = useToast();
  const dispatch = useAppDispatch();
  const activeSystem = useAppSelector(selectActiveSystem);

  const goBack = useCallback(() => {
    router.back();
    dispatch(setActiveSystem(undefined));
  }, [dispatch, router]);

  const handleSuccess = (system: System) => {
    dispatch(setActiveSystem(system));
    // TODO: more fleshed out toast message
    toast(successToastParams("System has been saved successfully"));
  };

  const tabData: TabData[] = [
    {
      label: "System information",
      content: (
        <Box px={6}>
          <SystemInformationForm
            onSuccess={handleSuccess}
            system={activeSystem}
            abridged={isCreate}
          />
        </Box>
      ),
    },
    {
      label: "Privacy declarations",
      content: activeSystem ? (
        <Box px={6}>
          <PrivacyDeclarationStep
            system={activeSystem as System}
            onCancel={goBack}
            onSuccess={goBack}
          />
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
      onChange={setTabIndex}
    />
  );
};

export default SystemFormTabs;
