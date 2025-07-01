import type { MenuProps } from "antd";
import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntSpace as Space,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import {
  ManualFieldListItem,
  ManualFieldStatus,
  ManualTaskFieldType,
} from "~/types/api";

import { useCompleteTaskMutation } from "../manual-tasks.slice";

interface Props {
  task: ManualFieldListItem;
}

export const ActionButtons = ({ task }: Props) => {
  const router = useRouter();
  const [completeTask, { isLoading: isCompleting }] = useCompleteTaskMutation();

  // Don't render anything for non-new tasks
  if (task.status !== ManualFieldStatus.NEW) {
    return null;
  }

  const handleComplete = () => {
    completeTask({
      task_id: task.manual_field_id,
      text_value: task.input_type === ManualTaskFieldType.TEXT ? "" : undefined,
      checkbox_value:
        task.input_type === ManualTaskFieldType.CHECKBOX ? false : undefined,
    });
  };

  const handleSkip = () => {
    // TODO: Implement skip functionality
  };

  const handleGoToRequest = () => {
    router.push({
      pathname: PRIVACY_REQUEST_DETAIL_ROUTE,
      query: { id: task.privacy_request.id },
    });
  };

  const menuItems: MenuProps["items"] = [
    {
      key: "skip",
      label: "Skip task",
      onClick: handleSkip,
    },
    {
      key: "go-to-request",
      label: "Go to request",
      onClick: handleGoToRequest,
    },
  ];

  return (
    <Space size="small">
      <Button
        type="default"
        onClick={handleComplete}
        size="small"
        loading={isCompleting}
      >
        Complete
      </Button>

      <Dropdown
        menu={{ items: menuItems }}
        trigger={["click"]}
        placement="bottomRight"
        overlayStyle={{ minWidth: 120 }}
      >
        <Button
          size="small"
          icon={<Icons.OverflowMenuVertical />}
          aria-label="More actions"
        />
      </Dropdown>
    </Space>
  );
};
