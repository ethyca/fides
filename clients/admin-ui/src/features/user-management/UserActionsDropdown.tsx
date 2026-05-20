import { Button, Dropdown, Icons, MenuProps, Modal, useMessage } from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";
import { useReinviteUserMutation } from "./user-management.slice";

interface UserActionsDropdownProps {
  user: User;
  onEdit: (userId: string) => void;
}

const UserActionsDropdown = ({ user, onEdit }: UserActionsDropdownProps) => {
  const message = useMessage();
  const loggedInUser = useAppSelector(selectUser);
  const [modal, contextHolder] = Modal.useModal();
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const canDelete = useHasPermission([ScopeRegistryEnum.USER_DELETE]);
  const canUpdate = useHasPermission([ScopeRegistryEnum.USER_UPDATE]);
  const canCreate = useHasPermission([ScopeRegistryEnum.USER_CREATE]);
  const isOwnProfile = loggedInUser ? loggedInUser.id === user.id : false;
  const canEdit = canUpdate || isOwnProfile;

  const [reinviteUser] = useReinviteUserMutation();

  const handleReinvite = () => {
    modal.confirm({
      title: "Reinvite user",
      content: `Are you sure you want to send a new invitation to ${user.username}?`,
      okText: "Reinvite",
      onOk: async () => {
        try {
          await reinviteUser(user.id).unwrap();
          message.success("Invitation sent.");
        } catch (error) {
          message.error(getErrorMessage(error));
        }
      },
    });
  };

  const items: MenuProps["items"] = [];

  if (canEdit) {
    items.push({
      key: "edit",
      label: "Edit",
      onClick: () => onEdit(user.id),
    });
  }

  if (user.has_invite && canCreate) {
    items.push({
      key: "reinvite",
      label: "Reinvite",
      onClick: handleReinvite,
    });
  }

  if (canDelete) {
    items.push(
      { type: "divider" },
      {
        key: "delete",
        label: "Delete",
        danger: true,
        onClick: () => setIsDeleteModalOpen(true),
      },
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <>
      {contextHolder}
      <Dropdown menu={{ items }} trigger={["click"]} placement="bottomRight">
        <Button
          size="small"
          type="text"
          icon={<Icons.OverflowMenuVertical />}
          onClick={(e) => e.stopPropagation()}
          aria-label={`Actions for ${user.username}`}
          data-testid={`user-actions-${user.id}`}
        />
      </Dropdown>
      <DeleteUserModal
        user={user}
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
      />
    </>
  );
};

export default UserActionsDropdown;
