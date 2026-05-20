import { Button, Icons, Select, Tag, Text, Tooltip, useMessage } from "fidesui";
import { useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CloudInfraGroupSummary } from "~/types/api";

import {
  useAssignResourcesToCloudInfraGroupMutation,
  useGetCloudInfraGroupsQuery,
  useUnassignResourcesFromCloudInfraGroupMutation,
} from "../../discovery-detection.slice";
import { CreateCloudInfraGroupModal } from "../components/CreateCloudInfraGroupModal";

const CREATE_NEW_GROUP_VALUE = "__create_new_group__";

const getGroupLabel = (group: {
  name?: string | null;
  system_name?: string | null;
  system_key?: string | null;
  id?: string;
}): string => {
  const groupName = group.name;
  const systemName = group.system_name || group.system_key;
  if (groupName && systemName) {
    return `${groupName} (${systemName})`;
  }
  return groupName || systemName || group.id || "Unnamed group";
};

interface GroupSelectProps {
  monitorId: string;
  resourceUrn: string;
  groups?: CloudInfraGroupSummary[] | null;
  disabled?: boolean;
}

export const GroupSelect = ({
  monitorId,
  resourceUrn,
  groups,
  disabled,
}: GroupSelectProps) => {
  const [open, setOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const messageApi = useMessage();

  const { data: availableGroups } = useGetCloudInfraGroupsQuery(
    { monitor_config_id: monitorId, size: 100 },
    { skip: !monitorId },
  );

  const [assignResources] = useAssignResourcesToCloudInfraGroupMutation();
  const [unassignResources] = useUnassignResourcesFromCloudInfraGroupMutation();

  const currentGroupIds = useMemo(
    () => (groups ?? []).map((g) => g.id),
    [groups],
  );

  const options = useMemo(() => {
    const groupOptions = (availableGroups?.items ?? []).map((group) => {
      const groupLabel = getGroupLabel(group);
      return {
        value: group.id,
        label: groupLabel,
        searchLabel: groupLabel,
      };
    });
    return [
      {
        value: CREATE_NEW_GROUP_VALUE,
        label: (
          <Text type="secondary">
            <Icons.Add className="mr-1 inline-block size-3" />
            Create new group...
          </Text>
        ),
        searchLabel: "create new group",
      },
      ...groupOptions,
    ];
  }, [availableGroups]);

  const handleSelect = async (groupId: string) => {
    if (groupId === CREATE_NEW_GROUP_VALUE) {
      setOpen(false);
      setIsCreateModalOpen(true);
      return;
    }

    setOpen(false);
    const result = await assignResources({
      monitor_config_id: monitorId,
      group_id: groupId,
      staged_resource_urns: [resourceUrn],
    });
    if (isErrorResult(result)) {
      messageApi.open({
        type: "error",
        content: getErrorMessage(result.error, "Failed to assign group."),
      });
    }
  };

  const handleDeselect = async (groupId: string) => {
    const group = (groups ?? []).find((g) => g.id === groupId);
    if (group?.assignment_promoted) {
      messageApi.open({
        type: "warning",
        content: "Cannot remove a promoted group assignment.",
      });
      return;
    }

    const result = await unassignResources({
      monitor_config_id: monitorId,
      group_id: groupId,
      staged_resource_urns: [resourceUrn],
    });
    if (isErrorResult(result)) {
      messageApi.open({
        type: "error",
        content: getErrorMessage(result.error, "Failed to remove group."),
      });
    }
  };

  const handleCreateSuccess = async (groupId: string) => {
    const result = await assignResources({
      monitor_config_id: monitorId,
      group_id: groupId,
      staged_resource_urns: [resourceUrn],
    });
    if (isErrorResult(result)) {
      messageApi.open({
        type: "error",
        content: getErrorMessage(
          result.error,
          "Group created, but failed to assign to this resource.",
        ),
      });
    }
  };

  const tagRender = (props: {
    value: string;
    label: React.ReactNode;
    closable: boolean;
    onClose: () => void;
  }) => {
    const { value, label } = props;
    const group = (groups ?? []).find((g) => g.id === value);
    const isPromoted = group?.assignment_promoted ?? false;

    const onPreventMouseDown = (event: React.MouseEvent<HTMLSpanElement>) => {
      event.preventDefault();
      event.stopPropagation();
    };

    return (
      <Tag
        color="white"
        bordered
        onMouseDown={onPreventMouseDown}
        closable={!isPromoted}
        onClose={(e) => {
          e.preventDefault();
          handleDeselect(value);
        }}
        icon={
          isPromoted ? <Icons.CheckmarkFilled color="#5a9a68" /> : undefined
        }
        style={{
          marginInlineEnd: "calc((var(--fidesui-padding-xs) * 0.5))",
        }}
      >
        <Text size="sm">{label}</Text>
      </Tag>
    );
  };

  return (
    <>
      <Select
        mode="multiple"
        showSearch={{ optionFilterProp: "searchLabel" }}
        value={currentGroupIds}
        options={options}
        onSelect={handleSelect}
        onDeselect={handleDeselect}
        prefix={
          <Tooltip title="Assign to group">
            <Button
              aria-label="Add Group"
              type="text"
              size="small"
              icon={<Icons.Add />}
              disabled={disabled}
            />
          </Tooltip>
        }
        placeholder=""
        suffixIcon={null}
        classNames={{
          root: "w-full max-w-full overflow-hidden p-0 cursor-pointer -ml-5",
        }}
        style={
          {
            "--fidesui-select-multiple-selector-bg-disabled": "transparent",
          } as React.CSSProperties
        }
        variant="borderless"
        autoFocus={false}
        maxTagCount="responsive"
        open={open}
        onOpenChange={(visible) => setOpen(visible)}
        tagRender={tagRender}
        disabled={disabled}
        popupMatchSelectWidth={400}
        aria-label="Assign groups"
        data-testid="group-select"
      />
      <CreateCloudInfraGroupModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        monitorId={monitorId}
        onSuccess={handleCreateSuccess}
      />
    </>
  );
};
