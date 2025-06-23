import type { MenuProps } from "antd";
import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntSpace as Space,
  Icons,
  useDisclosure,
} from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";

import { ManualTask } from "../mocked/types";
import { CompleteTaskModal } from "./CompleteTaskModal";

interface Props {
  task: ManualTask;
}

export const ActionButtons = ({ task }: Props) => {
  const router = useRouter();
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Don't render anything for non-new tasks
  if (task.status !== "new") {
    return null;
  }

  const handleComplete = () => {
    onOpen();
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
    <>
      <Space size="small">
        <Button type="default" onClick={handleComplete} size="small">
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

      <CompleteTaskModal isOpen={isOpen} onClose={onClose} task={task} />
    </>
  );
};
