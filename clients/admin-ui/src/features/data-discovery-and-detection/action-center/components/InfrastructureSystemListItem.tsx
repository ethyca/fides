import {
  Avatar,
  Button,
  Checkbox,
  Flex,
  Icons,
  List,
  Tag,
  Text,
  useMessage,
} from "fidesui";
import { useMemo } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { getBrandIconUrl, getDomain } from "~/features/common/utils";
import { tagRender } from "~/features/data-discovery-and-detection/action-center/fields/MonitorFieldListItem";
import { useUpdateInfrastructureSystemDataUsesMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { StagedResourceAPIResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import {
  INFRASTRUCTURE_DIFF_STATUS_COLOR,
  INFRASTRUCTURE_DIFF_STATUS_LABEL,
} from "../constants";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import InfrastructureClassificationSelect from "./InfrastructureClassificationSelect";
import { InfrastructureSystemActionsCell } from "./InfrastructureSystemActionsCell";

interface InfrastructureSystemListItemProps {
  item: StagedResourceAPIResponse;
  selected?: boolean;
  onSelect?: (key: string, selected: boolean) => void;
  onNavigate?: (url: string) => void;
  rowClickUrl?: (item: StagedResourceAPIResponse) => string;
  monitorId: string;
  activeTab?: ActionCenterTabHash | null;
  allowIgnore?: boolean;
  dataUsesDisabled?: boolean;
  onPromoteSuccess?: () => void;
}

export const InfrastructureSystemListItem = ({
  item,
  selected,
  onSelect,
  onNavigate,
  rowClickUrl,
  monitorId,
  activeTab,
  allowIgnore,
  dataUsesDisabled,
  onPromoteSuccess,
}: InfrastructureSystemListItemProps) => {
  const itemKey = item.urn;
  const url = rowClickUrl?.(item);
  const { metadata, diff_status: diffStatus } = item;
  const systemName = item.name ?? "Uncategorized";

  const messageApi = useMessage();

  const [updateDataUses] = useUpdateInfrastructureSystemDataUsesMutation();

  const handleUpdateDataUses = async (dataUses: string[]) => {
    const result = await updateDataUses({
      monitorId,
      dataUses,
      urn: itemKey,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    }
  };

  // Get logo URL: prefer vendor_logo_url, then try brandfetch, then use generic icon
  const logoUrl = useMemo(() => {
    // First priority: vendor logo URL from metadata (usually from brandfetch)
    if (metadata?.vendor_logo_url) {
      return metadata.vendor_logo_url;
    }

    // Second priority: try to get logo from brandfetch using vendor_id or system name
    const vendorId = item.vendor_id || systemName;
    if (vendorId && vendorId !== "Uncategorized") {
      try {
        // Try to extract domain from vendor ID or system name
        const domain = getDomain(vendorId);
        if (domain) {
          return getBrandIconUrl(domain, 36); // 18px * 2 for retina
        }
      } catch {
        // If domain extraction fails, continue to fallback
      }
    }

    return undefined;
  }, [metadata?.vendor_logo_url, item.vendor_id, systemName]);

  const handleClick = () => {
    if (url && onNavigate) {
      onNavigate(url);
    }
  };

  const handleCheckboxChange = (checked: boolean) => {
    if (onSelect && itemKey) {
      onSelect(itemKey, checked);
    }
  };

  // Handle data use selection
  const handleSelectDataUse = (value: string) => {
    const currentDataUses = item.preferred_data_uses ?? [];
    if (!currentDataUses.includes(value)) {
      handleUpdateDataUses([...currentDataUses, value]);
    }
  };

  return (
    <List.Item
      key={itemKey}
      actions={[
        <InfrastructureSystemActionsCell
          key="actions"
          monitorId={monitorId}
          system={item}
          allowIgnore={allowIgnore}
          activeTab={activeTab}
          onPromoteSuccess={onPromoteSuccess}
        />,
      ]}
    >
      <List.Item.Meta
        avatar={
          <Flex align="center" gap="small">
            <Checkbox
              checked={selected}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
              onClick={(e) => e.stopPropagation()}
            />
            <Avatar
              size={18}
              src={logoUrl}
              icon={<Icons.Settings />}
              alt={systemName}
            />
          </Flex>
        }
        title={
          <Flex gap="small" align="center" wrap="wrap">
            <Button type="text" size="small" onClick={handleClick}>
              <Text strong>{systemName}</Text>
            </Button>
            {diffStatus && INFRASTRUCTURE_DIFF_STATUS_LABEL[diffStatus] && (
              <Tag color={INFRASTRUCTURE_DIFF_STATUS_COLOR[diffStatus]}>
                {INFRASTRUCTURE_DIFF_STATUS_LABEL[diffStatus]}
              </Tag>
            )}
          </Flex>
        }
        description={
          <InfrastructureClassificationSelect
            mode="multiple"
            value={item.preferred_data_uses ?? []}
            urn={itemKey}
            tagRender={(props) => {
              // Show sparkle icon if the data use was auto-detected (in data_uses)
              // and not manually assigned (not in user_assigned_data_uses)
              const isAutoDetectedFromCompass = item.data_uses?.includes(
                props.value as string,
              );

              const handleClose = () => {
                const newDataUses =
                  item.preferred_data_uses?.filter(
                    (dataUse) => dataUse !== props.value,
                  ) ?? [];
                handleUpdateDataUses(newDataUses);
              };

              return tagRender({
                ...props,
                isFromClassifier: isAutoDetectedFromCompass,
                onClose: handleClose,
              });
            }}
            onSelectDataUse={handleSelectDataUse}
            disabled={dataUsesDisabled}
          />
        }
      />
    </List.Item>
  );
};
