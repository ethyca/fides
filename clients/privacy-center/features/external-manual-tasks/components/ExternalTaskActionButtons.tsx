/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/components/ActionButtons.tsx
 *
 * Key differences for external users:
 * - No "Go to request" navigation (external users don't have access)
 * - Simplified menu structure
 * - Uses external data-testids for Cypress testing
 * - Uses external Redux hooks and slice
 *
 * IMPORTANT: When updating admin-ui ActionButtons.tsx, review this component for sync!
 */

import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMenuProps as MenuProps,
  AntSpace as Space,
  Icons,
  useDisclosure,
} from "fidesui";

import { ManualTask } from "../types";
import { ExternalCompleteTaskModal } from "./ExternalCompleteTaskModal";
import { ExternalSkipTaskModal } from "./ExternalSkipTaskModal";

interface Props {
  task: ManualTask;
}

export const ExternalTaskActionButtons = ({ task }: Props) => {
  const {
    isOpen: isCompleteModalOpen,
    onOpen: onCompleteModalOpen,
    onClose: onCompleteModalClose,
  } = useDisclosure();
  const {
    isOpen: isSkipModalOpen,
    onOpen: onSkipModalOpen,
    onClose: onSkipModalClose,
  } = useDisclosure();

  // Don't render anything for non-new tasks
  if (task.status !== "new") {
    return null;
  }

  const handleComplete = () => {
    onCompleteModalOpen();
  };

  const handleSkip = () => {
    onSkipModalOpen();
  };

  const menuItems: MenuProps["items"] = [
    {
      key: "skip",
      label: "Skip task",
      onClick: handleSkip,
    },
  ];

  return (
    <>
      <Space size="small">
        <Button
          type="default"
          onClick={handleComplete}
          size="small"
          data-testid="task-complete-button"
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
            data-testid="task-actions-dropdown"
          />
        </Dropdown>
      </Space>

      <ExternalCompleteTaskModal
        isOpen={isCompleteModalOpen}
        onClose={onCompleteModalClose}
        task={task}
      />
      <ExternalSkipTaskModal
        isOpen={isSkipModalOpen}
        onClose={onSkipModalClose}
        task={task}
      />
    </>
  );
};
