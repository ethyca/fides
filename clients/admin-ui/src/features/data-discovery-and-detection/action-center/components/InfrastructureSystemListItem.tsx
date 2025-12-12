import {
  AntAvatar as Avatar,
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntSelectProps as SelectProps,
  AntTag as Tag,
  AntText as Text,
  Icons,
  SparkleIcon,
} from "fidesui";
import { useMemo } from "react";

import { getBrandIconUrl, getDomain } from "~/features/common/utils";
import { IdentityProviderApplicationMetadata } from "~/types/api/models/IdentityProviderApplicationMetadata";

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
  item: {
    id?: string | null;
    urn?: string;
    name?: string | null;
    system_key?: string | null;
    vendor_id?: string | null;
    metadata?: IdentityProviderApplicationMetadata | null;
    diff_status?: string | null;
    data_uses?: string[];
    description?: string | null;
    preferred_data_categories?: string[] | null;
    classifications?: Array<{ label: string }> | null;
  };
  selected?: boolean;
  onSelect?: (key: string, selected: boolean) => void;
  onNavigate?: (url: string) => void;
  rowClickUrl?: (item: InfrastructureSystemListItemProps["item"]) => string;
  monitorId: string;
  activeTab?: ActionCenterTabHash | null;
  allowIgnore?: boolean;
  onSetDataCategories?: (urn: string, dataCategories: string[]) => void;
  onSelectDataCategory?: (value: string) => void;
  dataCategoriesDisabled?: boolean;
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
  onSetDataCategories,
  onSelectDataCategory,
  dataCategoriesDisabled,
  onPromoteSuccess,
}: InfrastructureSystemListItemProps) => {
  const itemKey = item.urn ?? item.id ?? "";
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

  // Handle data category selection
  const handleSelectDataCategory = (value: string) => {
    if (onSelectDataCategory) {
      onSelectDataCategory(value);
    } else if (onSetDataCategories && itemKey) {
      const currentCategories = item.preferred_data_categories ?? [];
      if (!currentCategories.includes(value)) {
        onSetDataCategories(itemKey, [...currentCategories, value]);
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
            value={item.preferred_data_categories ?? []}
            urn={itemKey}
            tagRender={(props) => {
              const isFromClassifier = !!item.classifications?.find(
                (classification) => classification.label === props.value,
              );

              const handleClose = () => {
                if (onSetDataCategories && itemKey) {
                  const newDataCategories =
                    item.preferred_data_categories?.filter(
                      (category) => category !== props.value,
                    ) ?? [];
                  onSetDataCategories(itemKey, newDataCategories);
                }
              };

              return tagRender({
                ...props,
                isFromClassifier,
                onClose: handleClose,
              });
            }}
            onSelectDataCategory={handleSelectDataCategory}
            disabled={dataCategoriesDisabled}
          />
        }
      />
    </List.Item>
  );
};
