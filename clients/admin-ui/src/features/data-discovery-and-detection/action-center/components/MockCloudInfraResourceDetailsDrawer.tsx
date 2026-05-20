import {
  Avatar,
  DefaultOptionType,
  Descriptions,
  Flex,
  Icons,
  Typography,
} from "fidesui";
import { MouseEventHandler, useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { formatDate } from "~/features/common/utils";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";
import { DiffStatus } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { DetailsDrawer } from "../fields/DetailsDrawer";
import { DetailsAction } from "../fields/DetailsDrawer/types";
import {
  getServiceIconUrl,
  getServiceLabel,
} from "../utils/cloudInfraServiceInfo";

const { Text } = Typography;

const statusTagFor = (diffStatus?: DiffStatus | null) => {
  switch (diffStatus) {
    case DiffStatus.MONITORED:
      return { color: "success" as const, label: "Approved" };
    case DiffStatus.MUTED:
      return { color: "default" as const, label: "Ignored" };
    case DiffStatus.REMOVAL:
      return { color: "error" as const, label: "Removed" };
    default:
      return undefined;
  }
};

interface MockCloudInfraResourceDetailsDrawerProps {
  resource: CloudInfraStagedResource | null;
  open: boolean;
  onClose: () => void;
  assignedSystems: DefaultOptionType[];
  onAddSystem: (urn: string, system: DefaultOptionType) => void;
  onRemoveSystem: (
    urn: string,
    systemValue: DefaultOptionType["value"],
  ) => void;
  onApprove: (urn: string) => void;
  onIgnore: (urn: string) => void;
  onRestore: (urn: string) => void;
}

export const MockCloudInfraResourceDetailsDrawer = ({
  resource,
  open,
  onClose,
  assignedSystems,
  onAddSystem,
  onRemoveSystem,
  onApprove,
  onIgnore,
  onRestore,
}: MockCloudInfraResourceDetailsDrawerProps) => {
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);

  const onAddNewSystemClick: MouseEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    setIsNewSystemModalOpen(true);
  };
  if (!resource) {
    return (
      <DetailsDrawer
        itemKey=""
        open={open}
        onClose={onClose}
        title=""
        width={520}
      />
    );
  }

  const iconUrl = getServiceIconUrl(resource.service);
  const tagEntries = resource.tags ? Object.entries(resource.tags) : [];
  const status = statusTagFor(resource.diff_status);
  const isMuted = resource.diff_status === DiffStatus.MUTED;
  const hasAssigned = assignedSystems.length > 0;

  const titleIcon = (
    <Avatar
      src={iconUrl}
      shape="square"
      size="small"
      icon={
        <Icons.Layers
          style={{ color: "var(--fidesui-brand-minos)" }}
          className="m-1 size-full"
        />
      }
      className="bg-transparent"
      alt={resource.name ?? "Resource"}
    />
  );

  const items = [
    {
      key: "service",
      label: "Service",
      children: getServiceLabel(resource.service),
    },
    {
      key: "provider",
      label: "Provider",
      children: resource.meta?.provider?.toUpperCase() ?? "—",
    },
    {
      key: "region",
      label: "Region",
      children: resource.location,
    },
    {
      key: "account_id",
      label: "Account ID",
      children: resource.cloud_account_id,
    },
    {
      key: "monitor",
      label: "Monitor",
      children: resource.monitor_config_id ?? "—",
    },
    {
      key: "arn",
      label: "ARN",
      children: (
        <Flex align="center" gap="small" className="min-w-0">
          <Text
            code
            ellipsis={{ tooltip: resource.source_id }}
            className="min-w-0 flex-1 text-xs"
            data-testid="resource-arn"
          >
            {resource.source_id}
          </Text>
          <ClipboardButton copyText={resource.source_id} size="small" />
        </Flex>
      ),
    },
    {
      key: "source_type",
      label: "Source type",
      children: (
        <Text code className="text-xs">
          {resource.meta?.source_type ?? "—"}
        </Text>
      ),
    },
    {
      key: "approved",
      label: "Approved",
      children: resource.updated_at
        ? formatDate(new Date(resource.updated_at))
        : "—",
    },
    {
      key: "tags",
      label: "Tags",
      children:
        tagEntries.length === 0 ? (
          <Text type="secondary" className="text-xs">
            No tags
          </Text>
        ) : (
          <Flex gap="middle" wrap="wrap">
            {tagEntries.map(([k, v]) => (
              <Flex key={`${k}:${v}`} gap="small">
                <Text type="secondary">{k}:</Text>
                <Text>{v}</Text>
              </Flex>
            ))}
          </Flex>
        ),
    },
  ];

  const actions: DetailsAction[] = [
    isMuted
      ? {
          label: "Restore",
          callback: () => {
            onRestore(resource.urn);
            onClose();
          },
        }
      : {
          label: "Ignore",
          callback: () => {
            onIgnore(resource.urn);
            onClose();
          },
        },
    {
      label: "Approve",
      disabled: !hasAssigned || isMuted,
      callback: () => {
        onApprove(resource.urn);
        onClose();
      },
    },
  ];

  return (
    <>
      <DetailsDrawer
        itemKey={resource.urn}
        open={open}
        onClose={onClose}
        width={520}
        destroyOnHidden
        title={resource.name ?? "Resource"}
        titleIcon={titleIcon}
        titleTag={
          status
            ? {
                bordered: false,
                color: status.color,
                className: "font-normal text-[var(--fidesui-font-size-sm)]",
                children: status.label,
              }
            : undefined
        }
        actions={actions}
      >
        <Flex vertical gap="large">
          <Descriptions bordered size="small" column={1} items={items} />
          <Flex vertical gap={4}>
            <Text strong>Assigned systems</Text>
            <SystemSelect
              mode="multiple"
              labelInValue
              placeholder="Search systems..."
              style={{ width: "100%" }}
              value={assignedSystems}
              onAddSystem={onAddNewSystemClick}
              onSelect={(_, option) => onAddSystem(resource.urn, option)}
              onDeselect={(value) => {
                const optionValue =
                  typeof value === "object" &&
                  value !== null &&
                  "value" in value
                    ? (value as DefaultOptionType).value
                    : value;
                onRemoveSystem(resource.urn, optionValue);
              }}
              data-testid={`drawer-system-select-${resource.urn}`}
            />
          </Flex>
        </Flex>
      </DetailsDrawer>
      {isNewSystemModalOpen && (
        <AddNewSystemModal
          isOpen
          onClose={() => setIsNewSystemModalOpen(false)}
          onSuccessfulSubmit={(fidesKey, systemName) => {
            setIsNewSystemModalOpen(false);
            onAddSystem(resource.urn, {
              label: systemName,
              value: fidesKey,
            });
          }}
          toastOnSuccess
        />
      )}
    </>
  );
};
