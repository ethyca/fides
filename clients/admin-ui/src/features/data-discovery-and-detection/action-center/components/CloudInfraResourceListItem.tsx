import { Avatar, Flex, Icons, List, Tag, Text } from "fidesui";

import { INFRASTRUCTURE_DIFF_STATUS_COLOR } from "~/features/data-discovery-and-detection/action-center/constants";
import { DiffStatus } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import {
  getServiceIconUrl,
  getServiceLabel,
} from "../utils/cloudInfraServiceInfo";

interface CloudInfraResourceListItemProps {
  item: CloudInfraStagedResource;
}

export const CloudInfraResourceListItem = ({
  item,
}: CloudInfraResourceListItemProps) => {
  const resourceName = item.name ?? "Unnamed resource";

  return (
    <List.Item key={item.urn}>
      <Flex align="center" gap="middle" className="w-full">
        <List.Item.Meta
          avatar={
            <Avatar
              src={getServiceIconUrl(item.service)}
              shape="square"
              icon={
                <Icons.TransformInstructions
                  style={{ color: "var(--fidesui-minos)" }}
                  className="m-1 size-full"
                />
              }
              className="bg-transparent"
              alt={resourceName}
            />
          }
          title={
            <Flex gap="small" align="center" wrap="wrap">
              <Text strong>{resourceName}</Text>
              {item.diff_status === DiffStatus.MUTED && (
                <Tag color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.MUTED]}>
                  Ignored
                </Tag>
              )}
              {item.diff_status === DiffStatus.MONITORED && (
                <Tag
                  color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.MONITORED]}
                >
                  Approved
                </Tag>
              )}
              {item.diff_status === DiffStatus.REMOVAL && (
                <Tag
                  color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.REMOVAL]}
                >
                  Removed
                </Tag>
              )}
            </Flex>
          }
          description={
            <Flex vertical gap={4}>
              <Text type="secondary" ellipsis className="text-xs">
                {item.source_id}
              </Text>
              {item.tags && Object.keys(item.tags).length > 0 && (
                <Flex gap={4} wrap="wrap">
                  {Object.entries(item.tags).map(([key, value]) => (
                    <Tag key={key} className="text-xs" icon={<Icons.Tag />}>
                      {key}: {value}
                    </Tag>
                  ))}
                </Flex>
              )}
            </Flex>
          }
        />
        <Flex gap={4} wrap="wrap" className="shrink-0">
          {item.service && (
            <Tag color="terracotta">{getServiceLabel(item.service)}</Tag>
          )}
          {item.location && <Tag color="nectar">{item.location}</Tag>}
          {item.cloud_account_id && (
            <Tag color="sandstone">Account: {item.cloud_account_id}</Tag>
          )}
        </Flex>
      </Flex>
    </List.Item>
  );
};
