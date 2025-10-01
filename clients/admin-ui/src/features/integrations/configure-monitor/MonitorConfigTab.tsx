import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  useDisclosure,
} from "fidesui";
import { useState } from "react";

import { MonitorIcon } from "~/features/common/Icon/MonitorIcon";
import ConfigureMonitorModal from "~/features/integrations/configure-monitor/ConfigureMonitorModal";
import { useMonitorConfigTable } from "~/features/integrations/hooks/useMonitorConfigTable";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  MonitorConfig,
  SystemType,
} from "~/types/api";

import SharedConfigModal from "../SharedConfigModal";

const DATA_DISCOVERY_MONITOR_COPY = `A data discovery monitor observes configured systems for data model changes to proactively discover and classify data risks. Monitors can observe part or all of a project, dataset, table, or API for changes and each can be assigned to a different data steward.`;

const WEBSITE_MONITOR_COPY = `Configure your website monitor to identify active ad tech vendors and tracking technologies across your site. This monitor will analyze selected pages for vendor activity, compliance with privacy requirements, and data collection practices. Set your preferences below to customize the monitor frequency and scan locations.`;

const OKTA_MONITOR_COPY = `Configure your SSO provider monitor to detect and map systems within your infrastructure. This monitor will analyze connected systems to identify their activity and ensure accurate representation in your data map. Set your preferences below to customize the monitor&apos;s scan frequency and scope. To learn more about monitors, view our docs here.`;

const MONITOR_COPIES: Partial<Record<ConnectionType, string>> = {
  [ConnectionType.WEBSITE]: WEBSITE_MONITOR_COPY,
  [ConnectionType.OKTA]: OKTA_MONITOR_COPY,
} as const;

const MonitorConfigTab = ({
  integration,
  integrationOption,
}: {
  integration: ConnectionConfigurationResponse;
  integrationOption?: ConnectionSystemTypeMap;
}) => {
  const isWebsiteMonitor =
    integrationOption?.identifier === ConnectionType.WEBSITE;

  // Check if this is a SaaS type integration
  const isSaasIntegration = integrationOption?.type === SystemType.SAAS;

  const modal = useDisclosure();
  const [workingMonitor, setWorkingMonitor] = useState<
    MonitorConfig | undefined
  >(undefined);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [formStep, setFormStep] = useState(0);

  const handleEditMonitor = (monitor: MonitorConfig) => {
    setWorkingMonitor(monitor);
    setIsEditing(true);
    modal.onOpen();
  };

  const handleCloseModal = () => {
    setWorkingMonitor(undefined);
    setIsEditing(false);
    setFormStep(0);
    modal.onClose();
  };

  const handleAdvanceForm = (monitor: MonitorConfig) => {
    setWorkingMonitor(monitor);
    setFormStep(1);
  };

  // Use the new Ant Design table hook
  const { columns, tableProps, monitors, isLoading } = useMonitorConfigTable({
    integration,
    isWebsiteMonitor,
    onEditMonitor: handleEditMonitor,
  });

  const monitorCopy =
    MONITOR_COPIES[integrationOption?.identifier as ConnectionType] ??
    DATA_DISCOVERY_MONITOR_COPY;

  const getMonitorButtonState = () => {
    if (isSaasIntegration && monitors.length > 0) {
      return {
        isDisabled: true,
        tooltip: "API integrations only use a single monitor",
      };
    }
    const isLegacyConnection =
      !integration.name && integration.saas_config?.type === "salesforce";
    if (isLegacyConnection) {
      return {
        isDisabled: true,
        tooltip:
          "This is a legacy connection and cannot be used to create a monitor. Create a new Salesforce integration to use this feature.",
      };
    }

    return { isDisabled: false, tooltip: null };
  };

  const {
    isDisabled: isAddMonitorButtonDisabled,
    tooltip: addMonitorButtonTooltip,
  } = getMonitorButtonState();

  return (
    <>
      <Typography.Paragraph
        className="mb-6 max-w-3xl"
        data-testid="monitor-description"
      >
        {monitorCopy}
      </Typography.Paragraph>
      <Flex justify="space-between" className="py-3">
        <SharedConfigModal />
        <Tooltip title={addMonitorButtonTooltip}>
          <span>
            {/* This span wrapper is needed to ensure the tooltip works when the button is disabled */}
            <Button
              onClick={modal.onOpen}
              icon={<MonitorIcon />}
              iconPosition="end"
              data-testid="add-monitor-btn"
              disabled={isAddMonitorButtonDisabled}
            >
              Add monitor
            </Button>
          </span>
        </Tooltip>
      </Flex>
      <Table {...tableProps} loading={isLoading} columns={columns} />
      <ConfigureMonitorModal
        isOpen={modal.isOpen}
        onClose={handleCloseModal}
        formStep={formStep}
        onAdvance={handleAdvanceForm}
        monitor={workingMonitor}
        isEditing={isEditing}
        integration={integration}
        integrationOption={integrationOption!}
        isWebsiteMonitor={isWebsiteMonitor}
      />
    </>
  );
};

export default MonitorConfigTab;
