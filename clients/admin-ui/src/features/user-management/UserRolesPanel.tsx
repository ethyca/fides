/**
 * UserRolesPanel — Roles/Permissions tab content for the UserDrawer.
 *
 * Renders RolesForm (RBAC) or PermissionsForm (legacy) depending on
 * feature flags.  This is a thin wrapper that handles the "no user yet"
 * and "no permission" empty states so the drawer can render it
 * unconditionally.
 */

import { Flex, Spin, Typography } from "fidesui";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import PermissionsForm from "./PermissionsForm";
import RolesForm from "./RolesForm";
import { selectActiveUserId } from "./user-management.slice";

const { Text } = Typography;

const UserRolesPanel = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const { rbac: isRbacEnabled } = useFeatures();
  const canUpdateUserPermissions = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_UPDATE,
  ]);

  if (!activeUserId) {
    return (
      <Text type="secondary">
        Save the user profile first, then assign roles.
      </Text>
    );
  }

  if (!canUpdateUserPermissions) {
    return (
      <Text type="secondary">
        You do not have permission to manage roles for this user.
      </Text>
    );
  }

  if (isRbacEnabled) {
    return <RolesForm />;
  }

  return (
    <Flex vertical>
      <PermissionsForm />
    </Flex>
  );
};

export default UserRolesPanel;
