import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMenuProps as MenuProps,
  AntSpace as Space,
  Icons,
  useDisclosure,
} from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_REQUEST_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import {
  ManualFieldListItem,
  ManualFieldStatus,
  ScopeRegistryEnum,
} from "~/types/api";

import { CompleteTaskModal } from "./CompleteTaskModal";
import { SkipTaskModal } from "./SkipTaskModal";

interface Props {
  task: ManualFieldListItem;
}

export const ActionButtons = ({ task }: Props) => {
  const router = useRouter();
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

  // Check if user has permission to read privacy requests
  const hasPrivacyRequestReadAccess = useHasPermission([
    ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ]);

  // Don't render anything for non-new tasks
  if (task.status !== ManualFieldStatus.NEW) {
    return null;
  }

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
      onClick: onSkipModalOpen,
    },
  ];

  // Conditionally add "Go to request" if user has permission
  if (hasPrivacyRequestReadAccess) {
    menuItems.push({
      key: "go-to-request",
      label: "Go to request",
      onClick: handleGoToRequest,
    });
  }

  return (
    <>
      <Space size="small">
        <Button type="default" onClick={onCompleteModalOpen} size="small">
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

      <CompleteTaskModal
        isOpen={isCompleteModalOpen}
        onClose={onCompleteModalClose}
        task={task}
      />
      <SkipTaskModal
        isOpen={isSkipModalOpen}
        onClose={onSkipModalClose}
        task={task}
      />
    </>
  );
};
