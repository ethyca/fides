import {
  Avatar,
  Button,
  Checkbox,
  Flex,
  Icons,
  List,
  SelectProps,
  SparkleIcon,
  Tag,
  Text,
} from "fidesui";
import { useMemo } from "react";

import { getBrandIconUrl, getDomain } from "~/features/common/utils";
import { StagedResourceAPIResponse } from "~/types/api";

import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import InfrastructureClassificationSelect from "./InfrastructureClassificationSelect";
import { InfrastructureSystemActionsCell } from "./InfrastructureSystemActionsCell";

type TagRenderParams = Parameters<NonNullable<SelectProps["tagRender"]>>[0];

type TagRender = (
  props: TagRenderParams & {
    isFromClassifier?: boolean;
  },
) => ReturnType<NonNullable<SelectProps["tagRender"]>>;

const tagRender: TagRender = (props) => {
  const { label, closable, onClose, isFromClassifier } = props;

  const onPreventMouseDown = (event: React.MouseEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  return (
    <Tag
      color="white"
      bordered
      onMouseDown={onPreventMouseDown}
      closable={closable}
      onClose={onClose}
      style={{
        marginInlineEnd: "calc((var(--ant-padding-xs) * 0.5))",
      }}
      icon={isFromClassifier && <SparkleIcon />}
    >
      <Text size="sm">{label}</Text>
    </Tag>
  );
};

interface InfrastructureSystemListItemProps {
  item: StagedResourceAPIResponse;
  selected?: boolean;
  onSelect?: (key: string, selected: boolean) => void;
  onNavigate?: (url: string) => void;
  rowClickUrl?: (item: StagedResourceAPIResponse) => string;
  monitorId: string;
  activeTab?: ActionCenterTabHash | null;
  allowIgnore?: boolean;
  onSetDataUses?: (urn: string, dataUses: string[]) => void;
  onSelectDataUse?: (value: string) => void;
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
  onSetDataUses,
  onSelectDataUse,
  dataUsesDisabled,
  onPromoteSuccess,
}: InfrastructureSystemListItemProps) => {
  const itemKey = item.urn;
  const url = rowClickUrl?.(item);
  const { metadata } = item;
  const systemName = item.name ?? "Uncategorized";
  const systemType = metadata?.app_type ?? "System type";

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
    if (onSelectDataUse) {
      onSelectDataUse(value);
    } else if (onSetDataUses && itemKey) {
      const currentDataUses = item.preferred_data_uses ?? [];
      if (!currentDataUses.includes(value)) {
        onSetDataUses(itemKey, [...currentDataUses, value]);
      }
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
            <Text type="secondary" style={{ fontWeight: 400 }}>
              {systemType}
            </Text>
          </Flex>
        }
        description={
          <InfrastructureClassificationSelect
            mode="multiple"
            value={item.preferred_data_uses ?? []}
            urn={itemKey}
            tagRender={(props) => {
              const isFromClassifier = !!item.classifications?.find(
                (classification) => classification.label === props.value,
              );

              const handleClose = () => {
                if (onSetDataUses && itemKey) {
                  const newDataUses =
                    item.preferred_data_uses?.filter(
                      (dataUse) => dataUse !== props.value,
                    ) ?? [];
                  onSetDataUses(itemKey, newDataUses);
                }
              };

              return tagRender({
                ...props,
                isFromClassifier,
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
