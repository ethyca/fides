import { Button, Icons, Tag, Tooltip, Typography } from "fidesui";

import { useConnectionLogo } from "~/features/common/hooks";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import getIntegrationTypeInfo, {
  IntegrationTypeInfo,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { getCategoryLabel } from "~/features/integrations/utils/categoryUtils";
import { ConnectionConfigurationResponse } from "~/types/api";

const SelectableIntegrationBox = ({
  integration,
  integrationTypeInfo,
  onClick,
  onDetailsClick,
}: {
  integration?: ConnectionConfigurationResponse;
  integrationTypeInfo?: IntegrationTypeInfo;
  onClick?: () => void;
  onDetailsClick?: () => void;
}) => {
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
      className="cursor-pointer overflow-hidden rounded-lg border border-gray-200 p-3 transition-all duration-150 hover:border-gray-600 hover:bg-gray-50 hover:shadow-sm"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          onClick?.();
        }
      }}
      data-testid={`integration-info-${integration?.key}`}
    >
      <div className="flex w-full items-start justify-between">
        <div className="flex w-full grow">
          <ConnectionTypeLogo data={logoData} size={40} />
          <div className="mx-3 flex min-w-0 shrink grow flex-col">
            <div className="flex items-center gap-1">
              <Typography.Text
                strong
                style={{ fontSize: "14px" }}
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
            </div>
            <span className="mt-1 text-xs text-gray-500">
              {getCategoryLabel(typeInfo.category)}
            </span>
          </div>
          {onDetailsClick && (
            <Button
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onDetailsClick();
              }}
              type="default"
              className="shrink-0 px-2 py-1 text-xs"
              data-testid={`details-btn-${integration?.key}`}
            >
              Details
            </Button>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {typeInfo.tags.slice(0, 3).map((item) => (
          <Tag key={item}>{item}</Tag>
        ))}
        {typeInfo.tags.length > 3 && (
          <Tag color="corinth">+{typeInfo.tags.length - 3}</Tag>
        )}
      </div>
    </div>
  );
};

export default SelectableIntegrationBox;
