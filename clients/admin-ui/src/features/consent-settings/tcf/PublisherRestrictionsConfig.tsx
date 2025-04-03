import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton as Button,
  AntSpace as Space,
  AntSwitch as Switch,
  Skeleton,
  Text,
  useToast,
} from "fidesui";
import { useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams } from "~/features/common/toast";
import {
  useGetTCFConfigurationQuery,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf/tcf-config.slice";
import { isErrorResult } from "~/types/errors";

import DocsLink from "../../common/DocsLink";
import { useLocalStorage } from "../../common/hooks/useLocalStorage";
import QuestionTooltip from "../../common/QuestionTooltip";
import { usePatchConfigurationSettingsMutation } from "../../config-settings/config-settings.slice";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "../../plus/plus.slice";
import SettingsBox from "../SettingsBox";
import { CreateTCFConfigModal } from "./CreateTCFConfigModal";
import { PublisherRestrictionsTable } from "./PublisherRestrictionsTable";
import { TCFConfigurationDropdown } from "./TCFConfigurationDropdown";

const PUBLISHER_RESTRICTIONS_DOCS_URL =
  "https://ethyca.com/docs/tutorials/consent-management/consent-management-configuration/configure-tcf#vendor-overrides";

interface PublisherRestrictionsConfigProps {
  isTCFOverrideEnabled: boolean;
}

export const PublisherRestrictionsConfig = ({
  isTCFOverrideEnabled,
}: PublisherRestrictionsConfigProps) => {
  const [showTcfOverrideConfig, setShowTcfOverrideConfig] =
    useState<boolean>(isTCFOverrideEnabled);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTCFConfigId, setSelectedTCFConfigId] = useLocalStorage<
    string | null
  >("selectedTCFConfigId", null);
  const { data: tcfConfigurations, isLoading: isTcfConfigurationsLoading } =
    useGetTCFConfigurationsQuery(
      { page: 1, size: 50 },
      { skip: !isTCFOverrideEnabled },
    );

  const { data: selectedConfig, isFetching: isSelectedConfigLoading } =
    useGetTCFConfigurationQuery(selectedTCFConfigId || "", {
      skip: !selectedTCFConfigId,
    });

  // Automatically select first configuration when available
  useEffect(() => {
    if (tcfConfigurations?.items?.length && !selectedTCFConfigId) {
      setSelectedTCFConfigId(tcfConfigurations.items[0].id);
    }
  }, [tcfConfigurations?.items, selectedTCFConfigId, setSelectedTCFConfigId]);

  const toast = useToast();

  const { isLoading: isHealthCheckLoading } = useGetHealthQuery();
  const [
    patchConfigSettingsTrigger,
    { isLoading: isPatchConfigSettingsLoading },
  ] = usePatchConfigurationSettingsMutation();
  const [patchTcfPurposeOverridesTrigger] =
    usePatchTcfPurposeOverridesMutation();
  const { data: tcfPurposeOverrides } = useGetTcfPurposeOverridesQuery(
    undefined,
    {
      skip: isHealthCheckLoading,
    },
  );

  const handleOverrideOnChange = async (checked: boolean) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      toast.closeAll();
      setShowTcfOverrideConfig(checked);
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving vendor override settings. Please try again.`,
        );
        setShowTcfOverrideConfig(false);
        toast(errorToastParams(errorMsg));
      }
    };

    const result = await patchConfigSettingsTrigger({
      consent: {
        override_vendor_purposes: checked,
      },
    });

    if (checked && tcfPurposeOverrides) {
      await patchTcfPurposeOverridesTrigger(
        tcfPurposeOverrides.map((po) => ({
          ...po,
          is_included: true,
          required_legal_basis: undefined,
        })),
      );
    }

    handleResult(result);
  };

  return (
    <SettingsBox title="Publisher restrictions" fontSize="sm">
      <Space direction="vertical" size="small">
        <Text>Configure overrides for TCF related purposes.</Text>
        {/* eslint-disable-next-line no-nested-ternary */}
        {isTcfConfigurationsLoading ? (
          <>
            <Skeleton height="20px" />
            <Skeleton height="20px" />
          </>
        ) : tcfConfigurations?.items?.length ? (
          <>
            <Space size="small">
              <Switch
                size="small"
                defaultChecked={showTcfOverrideConfig}
                onChange={handleOverrideOnChange}
                disabled={isPatchConfigSettingsLoading}
              />
              <Text>Override vendor purposes</Text>
              <QuestionTooltip label="Toggle on if you want to globally change any flexible legal bases or remove TCF purposes from your CMP" />
            </Space>
            {showTcfOverrideConfig && (
              <>
                <Text>
                  The table below allows you to adjust which TCF purposes you
                  allow as part of your user facing notices and business
                  activities.
                </Text>
                <Text>
                  To configure this section, select a TCF purpose to edit the
                  restriction type and vendors.{" "}
                  <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                    Learn more about publisher restrictions
                  </DocsLink>{" "}
                  in our docs.
                </Text>
                <TCFConfigurationDropdown
                  selectedConfigId={selectedTCFConfigId || ""}
                  configurations={tcfConfigurations?.items || []}
                  isLoading={isTcfConfigurationsLoading}
                  onConfigurationSelect={setSelectedTCFConfigId}
                />
              </>
            )}
          </>
        ) : (
          <>
            <Text>
              To define custom publisher restrictions select &quot;create
              configuration&quot; below.{" "}
              <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                Learn more about publisher restrictions
              </DocsLink>{" "}
              in our docs.
            </Text>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              Create configuration +
            </Button>
          </>
        )}
      </Space>
      <CreateTCFConfigModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={(configId) => {
          setSelectedTCFConfigId(configId);
        }}
      />
      {showTcfOverrideConfig && (
        <PublisherRestrictionsTable
          className="mt-3"
          config={selectedConfig}
          isLoading={isSelectedConfigLoading}
        />
      )}
    </SettingsBox>
  );
};
