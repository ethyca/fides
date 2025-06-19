import type { MenuProps } from "antd";
import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntSpace as Space,
  Icons,
} from "fidesui";

import { ManualTask } from "~/types/api/models/ManualTask";

import { useCompleteTaskMutation } from "../manual-tasks.slice";

interface Props {
  task: ManualTask;
}

export const ActionButtons = ({ task }: Props) => {
  const [completeTask, { isLoading: isCompleting }] = useCompleteTaskMutation();

  // Don't render anything for non-new tasks
  if (task.status !== "new") {
    return null;
  }

  const handleComplete = () => {
    completeTask({
      task_id: task.task_id,
      text_value: task.input_type === "string" ? "" : undefined,
      checkbox_value: task.input_type === "checkbox" ? false : undefined,
    });
  };

  const handleSkip = () => {
    // TODO: Implement skip functionality
    console.log("Skip button clicked for task:", task.task_id);
  };

  const menuItems: MenuProps["items"] = [
    {
      key: "skip",
      label: "Skip",
      onClick: handleSkip,
    },
  ];

  return (
    <Space size="small">
      <Button
        type="primary"
        onClick={handleComplete}
        size="small"
        loading={isCompleting}
      >
        Complete
      </Button>

      <Dropdown
        menu={{ items: menuItems }}
        trigger={["hover"]}
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
