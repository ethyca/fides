import { utf8ToB64 } from "common/utils";
import {
  Button,
  Drawer,
  Flex,
  Icons,
  Spin,
  Tabs,
  Typography,
} from "fidesui";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { isErrorResult } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum, UserCreateExtended } from "~/types/api";

import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";
import {
  setActiveUserId,
  useCreateUserMutation,
  useEditUserMutation,
  useGetUserByIdQuery,
} from "./user-management.slice";
import UserProfileForm from "./UserProfileForm";
import UserRolesPanel from "./UserRolesPanel";

const { Text } = Typography;

interface UserDrawerProps {
  userId: string | null;
  onClose: () => void;
}

const UserDrawer = ({ userId, onClose }: UserDrawerProps) => {
  const dispatch = useAppDispatch();
  const currentUser = useSelector(selectUser);
  const { rbac: isRbacEnabled } = useFeatures();

  const isNewUser = userId === "new";
  const isOpen = userId !== null;

  const {
    data: user,
    isLoading,
    error,
  } = useGetUserByIdQuery(userId as string, {
    skip: !userId || isNewUser,
  });

  // Keep activeUserId in sync for PasswordManagement / RolesForm / PermissionsForm
  useEffect(() => {
    if (isNewUser) {
      dispatch(setActiveUserId(undefined));
    } else if (user) {
      dispatch(setActiveUserId(user.id));
    }
  }, [dispatch, user, isNewUser]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      dispatch(setActiveUserId(undefined));
    };
  }, [dispatch]);

  // Permissions
  const canUserUpdate = useHasPermission([ScopeRegistryEnum.USER_UPDATE]);
  const canUserDelete = useHasPermission([ScopeRegistryEnum.USER_DELETE]);
  const canUpdatePermissions = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_UPDATE,
  ]);

  const isOwnProfile = currentUser && user ? currentUser.id === user.id : false;
  const canEditNames = isOwnProfile || canUserUpdate;

  // Mutations
  const [createUser] = useCreateUserMutation();
  const [editUser] = useEditUserMutation();

  const handleSubmit = async (values: UserCreateExtended) => {
    if (isNewUser) {
      const b64Password = values.password
        ? utf8ToB64(values.password)
        : undefined;
      const result = await createUser({
        ...values,
        password: b64Password,
      });
      if (!isErrorResult(result)) {
        // Switch drawer to the newly created user
        dispatch(setActiveUserId(result.data.id));
      }
      return result;
    }
    return editUser({ ...values, id: user!.id });
  };

  // Delete modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleDelete = () => {
    setIsDeleteModalOpen(false);
    onClose();
  };

  // Tab config
  const rolesTabDisabled = isNewUser || !canUpdatePermissions;

  const drawerTitle = isNewUser
    ? "New user"
    : user?.username ?? "User profile";

  const tabs = [
    {
      label: "Profile",
      key: "profile",
      children: (
        <UserProfileForm
          user={isNewUser ? undefined : user}
          onSubmit={handleSubmit}
          canEditNames={canEditNames}
        />
      ),
    },
    {
      label: isRbacEnabled ? "Roles" : "Permissions",
      key: "roles",
      disabled: rolesTabDisabled,
      children: <UserRolesPanel />,
      forceRender: !rolesTabDisabled,
    },
  ];

  return (
    <>
      <Drawer
        open={isOpen}
        onClose={onClose}
        placement="right"
        width={560}
        title={drawerTitle}
        destroyOnHidden
        extra={
          !isNewUser && user && canUserDelete ? (
            <Button
              size="small"
              icon={<Icons.TrashCan />}
              onClick={() => setIsDeleteModalOpen(true)}
              aria-label="Delete user"
              data-testid="drawer-delete-user-btn"
            />
          ) : undefined
        }
      >
        {isLoading && !isNewUser ? (
          <Flex justify="center" align="center" style={{ padding: 40 }}>
            <Spin />
          </Flex>
        ) : error ? (
          <Text type="danger">Failed to load user profile.</Text>
        ) : (
          <Tabs items={tabs} />
        )}
      </Drawer>

      {user && (
        <DeleteUserModal
          user={user}
          isOpen={isDeleteModalOpen}
          onClose={handleDelete}
        />
      )}
    </>
  );
};

export default UserDrawer;
