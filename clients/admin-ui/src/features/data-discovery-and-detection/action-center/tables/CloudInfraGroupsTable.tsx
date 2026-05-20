import {
  Button,
  Empty,
  Flex,
  Icons,
  List,
  Pagination,
  Tag,
  Text,
  Tooltip,
  useMessage,
  useModal,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { CloudInfraGroupResponse } from "~/types/api";

import {
  useDeleteCloudInfraGroupMutation,
  useGetCloudInfraGroupsQuery,
} from "../../discovery-detection.slice";
import { CreateCloudInfraGroupModal } from "../components/CreateCloudInfraGroupModal";

interface CloudInfraGroupsTableProps {
  monitorId: string;
}

export const CloudInfraGroupsTable = ({
  monitorId,
}: CloudInfraGroupsTableProps) => {
  const { paginationProps, pageIndex, pageSize } = useAntPagination({
    defaultPageSize: 25,
  });
  const { data, isLoading } = useGetCloudInfraGroupsQuery(
    {
      monitor_config_id: monitorId,
      page: pageIndex,
      size: pageSize,
    },
    { refetchOnMountOrArgChange: true },
  );
  const [deleteGroup] = useDeleteCloudInfraGroupMutation();
  const messageApi = useMessage();
  const modalApi = useModal();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<
    CloudInfraGroupResponse | undefined
  >();

  const handleDelete = async (group: CloudInfraGroupResponse) => {
    const groupLabel = group.name || group.system_name || "this group";
    const confirmed = await modalApi.confirm({
      title: "Delete group",
      content: `Are you sure you want to delete "${groupLabel}"? Resource assignments will be lost.`,
      okText: "Delete",
      okButtonProps: { danger: true },
      icon: null,
    });
    if (!confirmed) {
      return;
    }
    const result = await deleteGroup({
      monitor_config_id: monitorId,
      group_id: group.id,
    });
    if (isErrorResult(result)) {
      messageApi.open({
        type: "error",
        content: getErrorMessage(result.error, "Failed to delete group."),
      });
      return;
    }
    messageApi.open({ type: "success", content: "Group deleted." });
  };

  return (
    <Flex vertical gap="middle" className="h-full overflow-hidden">
      <Flex justify="space-between" align="center">
        <Text type="secondary">
          {data?.total ?? 0} group{data?.total !== 1 ? "s" : ""}
        </Text>
        <Button
          type="primary"
          icon={<Icons.Add />}
          onClick={() => setIsCreateModalOpen(true)}
          data-testid="create-group-btn"
        >
          Create group
        </Button>
      </Flex>
      <Flex flex={1} style={{ minHeight: 0, overflow: "hidden" }}>
        <List
          dataSource={data?.items}
          loading={isLoading}
          className="size-full overflow-y-auto overflow-x-clip"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No groups yet"
              />
            ),
          }}
          renderItem={(group) => (
            <List.Item
              key={group.id}
              actions={[
                <Text key="counts" type="secondary" className="text-xs">
                  Total resources: {group.resource_count}
                  {group.promoted_resource_count > 0 &&
                    `, Promoted: ${group.promoted_resource_count}`}
                </Text>,
                <Button
                  key="edit"
                  size="small"
                  icon={<Icons.Edit />}
                  aria-label="Edit group"
                  onClick={() => setEditingGroup(group)}
                />,
                <Tooltip
                  key="delete"
                  title={
                    group.promoted_resource_count > 0
                      ? "Cannot delete: group has promoted resources"
                      : undefined
                  }
                >
                  <Button
                    size="small"
                    icon={<Icons.TrashCan />}
                    aria-label="Delete group"
                    disabled={group.promoted_resource_count > 0}
                    onClick={() => handleDelete(group)}
                  />
                </Tooltip>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Flex gap="small" align="center">
                    <Text strong>
                      {group.name || group.system_name || "Unnamed group"}
                    </Text>
                    {group.promoted_resource_count === 0 && (
                      <Tag color="default">Draft</Tag>
                    )}
                  </Flex>
                }
                description={
                  <Flex gap="small">
                    <Text type="secondary">System:</Text>
                    {group.system_name ? (
                      <Text>{group.system_name}</Text>
                    ) : (
                      <Text type="secondary" italic>
                        Not assigned
                      </Text>
                    )}
                  </Flex>
                }
              />
            </List.Item>
          )}
        />
      </Flex>
      <Pagination
        {...paginationProps}
        total={data?.total || 0}
        showSizeChanger={{ suffixIcon: <Icons.ChevronDown /> }}
        hideOnSinglePage
      />
      <CreateCloudInfraGroupModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        monitorId={monitorId}
      />
      {editingGroup && (
        <CreateCloudInfraGroupModal
          isOpen
          onClose={() => setEditingGroup(undefined)}
          monitorId={monitorId}
          group={editingGroup}
        />
      )}
    </Flex>
  );
};
