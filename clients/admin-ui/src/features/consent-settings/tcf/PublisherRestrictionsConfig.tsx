import { Button, Skeleton, Space, Typography } from "fidesui";
import { useEffect, useState } from "react";

import {
  useGetTCFConfigurationQuery,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf/tcf-config.slice";

import DocsLink from "../../common/DocsLink";
import { useLocalStorage } from "../../common/hooks/useLocalStorage";
import SettingsBox from "../SettingsBox";
import { PUBLISHER_RESTRICTIONS_DOCS_URL } from "./constants";
import { CreateTCFConfigModal } from "./CreateTCFConfigModal";
import { PublisherRestrictionsTable } from "./PublisherRestrictionsTable";
import { TCFConfigurationDropdown } from "./TCFConfigurationDropdown";
import { TCFOverrideToggle } from "./TCFOverrideToggle";

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
    if (
      !isTcfConfigurationsLoading &&
      tcfConfigurations?.items?.length &&
      !selectedTCFConfigId
    ) {
      setSelectedTCFConfigId(tcfConfigurations.items[0].id);
    }
    if (
      !isTcfConfigurationsLoading &&
      selectedTCFConfigId &&
      !tcfConfigurations?.items?.length
    ) {
      setSelectedTCFConfigId(null);
    }
  }, [
    isTcfConfigurationsLoading,
    tcfConfigurations?.items,
    selectedTCFConfigId,
    setSelectedTCFConfigId,
  ]);

  return (
    <SettingsBox title="Publisher restrictions">
      <Space orientation="vertical" size="small" style={{ width: "100%" }}>
        <TCFOverrideToggle
          defaultChecked={showTcfOverrideConfig}
          onChange={(checked) => setShowTcfOverrideConfig(checked)}
        />
        {showTcfOverrideConfig && (
          <>
            {isTcfConfigurationsLoading && (
              <>
                <Skeleton.Input active block />
                <Skeleton.Input active block />
                <Skeleton.Input active style={{ width: 200 }} />
              </>
            )}
            {!isTcfConfigurationsLoading && tcfConfigurations?.items?.length ? (
              <>
                <Typography.Paragraph>
                  The table below allows you to adjust which TCF purposes you
                  allow as part of your user facing notices and business
                  activities.
                </Typography.Paragraph>
                <Typography.Paragraph>
                  To configure this section, select a TCF purpose to edit the
                  restriction type and vendors.{" "}
                  <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                    Learn more about publisher restrictions
                  </DocsLink>{" "}
                  in our docs.
                </Typography.Paragraph>
                <TCFConfigurationDropdown
                  selectedConfigId={selectedTCFConfigId || ""}
                  configurations={tcfConfigurations?.items || []}
                  onConfigurationSelect={setSelectedTCFConfigId}
                />
              </>
            ) : (
              <>
                <Typography.Paragraph>
                  To define custom publisher restrictions select &quot;create
                  configuration&quot; below.{" "}
                  <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                    Learn more about publisher restrictions
                  </DocsLink>{" "}
                  in our docs.
                </Typography.Paragraph>
                <Button
                  onClick={() => setIsCreateModalOpen(true)}
                  data-testid="create-config-button"
                >
                  Create configuration +
                </Button>
              </>
            )}
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
      {showTcfOverrideConfig && selectedTCFConfigId && (
        <PublisherRestrictionsTable
          className="mt-3"
          config={selectedConfig}
          isLoading={isSelectedConfigLoading}
        />
      )}
    </SettingsBox>
  );
};
