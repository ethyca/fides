import {
  AntButton as Button,
  AntSpace as Space,
  Skeleton,
  Text,
} from "fidesui";
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
    if (tcfConfigurations?.items?.length && !selectedTCFConfigId) {
      setSelectedTCFConfigId(tcfConfigurations.items[0].id);
    }
    if (selectedTCFConfigId && !tcfConfigurations?.items?.length) {
      setSelectedTCFConfigId(null);
    }
  }, [tcfConfigurations?.items, selectedTCFConfigId, setSelectedTCFConfigId]);

  return (
    <SettingsBox title="Publisher restrictions" fontSize="sm">
      <Space direction="vertical" size="small" style={{ width: "100%" }}>
        <TCFOverrideToggle
          defaultChecked={showTcfOverrideConfig}
          onChange={(checked) => setShowTcfOverrideConfig(checked)}
        />
        {showTcfOverrideConfig && (
          <>
            {isTcfConfigurationsLoading && (
              <>
                <Skeleton height="20px" />
                <Skeleton height="20px" />
                <Skeleton height="32px" width="200px" />
              </>
            )}
            {!isTcfConfigurationsLoading && tcfConfigurations?.items?.length ? (
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
                  onConfigurationSelect={setSelectedTCFConfigId}
                />
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
