import {
  Button,
  DefaultOptionType,
  Flex,
  Form,
  Input,
  Modal,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CloudInfraGroupResponse } from "~/types/api";

import {
  useCreateCloudInfraGroupMutation,
  useUpdateCloudInfraGroupMutation,
} from "../../discovery-detection.slice";

const { Text } = Typography;

interface CreateCloudInfraGroupModalProps {
  isOpen: boolean;
  onClose: () => void;
  monitorId: string;
  onSuccess?: (groupId: string) => void;
  /** When provided, the modal operates in edit mode. */
  group?: CloudInfraGroupResponse;
}

export const CreateCloudInfraGroupModal = ({
  isOpen,
  onClose,
  monitorId,
  onSuccess,
  group,
}: CreateCloudInfraGroupModalProps) => {
  const isEditMode = !!group;

  const [groupName, setGroupName] = useState("");
  const [selectedSystem, setSelectedSystem] = useState<
    DefaultOptionType | undefined
  >();
  const [createGroup, { isLoading: isCreating }] =
    useCreateCloudInfraGroupMutation();
  const [updateGroup, { isLoading: isUpdating }] =
    useUpdateCloudInfraGroupMutation();
  const messageApi = useMessage();

  const isLoading = isCreating || isUpdating;

  // Pre-fill values when editing
  useEffect(() => {
    if (group && isOpen) {
      setGroupName(group.name ?? "");
      if (group.system_key) {
        setSelectedSystem({
          value: group.system_key,
          label: group.system_name ?? group.system_key,
        });
      } else {
        setSelectedSystem(undefined);
      }
    }
  }, [group, isOpen]);

  const hasName = groupName.trim().length > 0;
  const hasSystem = !!selectedSystem;
  const canSubmit = hasName || hasSystem;

  const handleClose = () => {
    setGroupName("");
    setSelectedSystem(undefined);
    onClose();
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      return;
    }
    const body = {
      name: hasName ? groupName.trim() : undefined,
      system_key: hasSystem ? (selectedSystem.value as string) : undefined,
    };

    if (isEditMode) {
      const result = await updateGroup({
        monitor_config_id: monitorId,
        group_id: group.id,
        body,
      });
      if (isErrorResult(result)) {
        messageApi.open({
          type: "error",
          content: getErrorMessage(result.error, "Failed to update group."),
        });
        return;
      }
      messageApi.open({ type: "success", content: "Group updated." });
      handleClose();
      onSuccess?.(group.id);
    } else {
      const result = await createGroup({
        monitor_config_id: monitorId,
        body,
      });
      if (isErrorResult(result)) {
        messageApi.open({
          type: "error",
          content: getErrorMessage(result.error, "Failed to create group."),
        });
        return;
      }
      const label =
        result.data.system_name || result.data.name || "Unnamed group";
      messageApi.open({
        type: "success",
        content: `Group "${label}" created.`,
      });
      handleClose();
      onSuccess?.(result.data.id);
    }
  };

  return (
    <Modal
      title={isEditMode ? "Edit group" : "Create group"}
      open={isOpen}
      onCancel={handleClose}
      centered
      destroyOnHidden
      footer={null}
      data-testid="create-cloud-infra-group-modal"
    >
      <Flex vertical gap={20} className="pb-6 pt-4">
        <Text>
          {isEditMode
            ? "Update the group name or change the system it targets."
            : "Group resources into a System. Provide a name for a new system, or select an existing one. The system will be created when a resource in this group is promoted."}
        </Text>
        <Form layout="vertical">
          <Form.Item label="Group name" className="mb-4">
            <Input
              placeholder="e.g. Payment Processing"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              onPressEnter={handleSubmit}
              data-testid="group-name-input"
            />
          </Form.Item>
          <Form.Item label="Existing system" className="mb-0">
            <SystemSelect
              placeholder="Search or select a system..."
              onSelect={(_, option) => setSelectedSystem(option)}
              value={selectedSystem}
              allowClear
              onClear={() => setSelectedSystem(undefined)}
            />
          </Form.Item>
        </Form>
      </Flex>
      <Flex justify="space-between">
        <Button htmlType="reset" onClick={handleClose} data-testid="cancel-btn">
          Cancel
        </Button>
        <Button
          htmlType="submit"
          type="primary"
          disabled={!canSubmit}
          loading={isLoading}
          onClick={handleSubmit}
          data-testid="save-btn"
        >
          {isEditMode ? "Save" : "Create"}
        </Button>
      </Flex>
    </Modal>
  );
};
