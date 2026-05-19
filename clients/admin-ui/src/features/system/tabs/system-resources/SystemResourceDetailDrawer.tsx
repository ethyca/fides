import { Descriptions, Drawer, Flex, Tag, Typography } from "fidesui";

import ClipboardButton from "~/features/common/ClipboardButton";
import { formatDate } from "~/features/common/utils";
import { getServiceLabel } from "~/features/data-discovery-and-detection/action-center/utils/cloudInfraServiceInfo";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

const { Text } = Typography;

const SystemResourceDetailDrawer = ({
  resource,
  isOpen,
  onClose,
}: {
  resource: CloudInfraStagedResource | null;
  isOpen: boolean;
  onClose: () => void;
}) => {
  const tags = resource?.tags ?? {};
  const tagEntries = Object.entries(tags);

  const items = resource
    ? [
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
            <Flex align="center" gap="small">
              <Text
                code
                className="break-all text-xs"
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
              <Text type="secondary" className="text-sm">
                No tags
              </Text>
            ) : (
              <Flex gap={4} wrap="wrap">
                {tagEntries.map(([k, v]) => (
                  <Tag key={`${k}:${v}`} className="text-xs">
                    {k}: {v}
                  </Tag>
                ))}
              </Flex>
            ),
        },
      ]
    : [];

  return (
    <Drawer
      open={isOpen}
      onClose={onClose}
      width={520}
      destroyOnHidden
      title={resource?.name ?? "Resource"}
    >
      {resource && (
        <Descriptions
          bordered
          size="small"
          column={1}
          items={items}
          data-testid="resource-detail-drawer"
        />
      )}
    </Drawer>
  );
};

export default SystemResourceDetailDrawer;
