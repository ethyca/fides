import { Button, Flex, Icons, Tag, Tooltip, Typography } from "fidesui";

import { useConnectionLogo } from "~/features/common/hooks";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import styles from "~/features/integrations/SelectableIntegrationBox.module.scss";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionConfigurationResponse } from "~/types/api";

interface SelectableIntegrationBoxProps {
  integration?: ConnectionConfigurationResponse;
  integrationTypeInfo?: IntegrationTypeInfo;
  onClick?: () => void;
  onDetailsClick?: () => void;
}

const SelectableIntegrationBox = ({
  integration,
  integrationTypeInfo,
  onClick,
  onDetailsClick,
}: SelectableIntegrationBoxProps) => {
  const logoData = useConnectionLogo(integration);

  const typeInfo =
    integrationTypeInfo ||
    getIntegrationTypeInfo(
      integration?.connection_type,
      integration?.saas_config?.type,
    );

  const connectionOption = useIntegrationOption(
    integration?.connection_type,
    integration?.saas_config?.type as SaasConnectionTypes,
  );

  return (
    <div
      className={`cursor-pointer overflow-hidden p-3 ${styles.card}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      data-testid={`integration-info-${integration?.key}`}
    >
      <Flex justify="space-between" align="start" className="w-full">
        <Flex className="w-full grow">
          <ConnectionTypeLogo data={logoData} size={40} />
          <Flex vertical className="mx-3 min-w-0 shrink grow">
            <Flex align="center" gap="small">
              <Typography.Text
                strong
                ellipsis={{
                  tooltip: integration?.name || "(No name)",
                }}
              >
                {integration?.name || "(No name)"}
              </Typography.Text>
              {connectionOption?.custom && (
                <Tooltip title="Custom integration" placement="top">
                  <span className="inline-flex">
                    <Icons.SettingsCheck size={16} />
                  </span>
                </Tooltip>
              )}
            </Flex>
            <Typography.Text
              type="secondary"
              className={`mt-1 ${styles.categoryLabel}`}
            >
              {getCategoryLabel(typeInfo.category)}
            </Typography.Text>
          </Flex>
          {onDetailsClick && (
            <Button
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onDetailsClick();
              }}
              type="default"
              className="shrink-0 px-2 py-1"
              data-testid={`details-btn-${integration?.key}`}
            >
              Details
            </Button>
          )}
        </Flex>
      </Flex>
      <Flex wrap gap={4} className="mt-3">
        {typeInfo.tags.slice(0, 3).map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
        {typeInfo.tags.length > 3 && (
          <Tag color="corinth">+{typeInfo.tags.length - 3}</Tag>
        )}
      </Flex>
    </div>
  );
};

export default SelectableIntegrationBox;
