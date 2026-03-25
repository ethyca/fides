import { Flex, Tabs } from "fidesui";
import RoleDescriptionDrawer from "user-management/RoleDescriptionDrawer";

import { useAppSelector } from "~/app/hooks";
import { useFlags } from "~/features/common/features";
import { ScopeRegistryEnum } from "~/types/api";

import { useHasPermission } from "../common/Restrict";
import PermissionsForm from "./PermissionsForm";
import RolesForm from "./RolesForm";
import {
  selectActiveUserId,
  useGetUserByIdQuery,
} from "./user-management.slice";
import UserForm, { type UserFormProps } from "./UserForm";

const UserManagementTabs = ({
  onSubmit,
  initialValues,
  ...props
}: UserFormProps) => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const { flags } = useFlags();
  const isRbacEnabled = flags.alphaRbac;

  // Subscribe to active user
  useGetUserByIdQuery(activeUserId as string, { skip: !activeUserId });

  const canUpdateUserPermissions = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_UPDATE,
  ]);

  // If it is a new user, or if the user does not have permission
  const rolesTabDisabled = !activeUserId || !canUpdateUserPermissions;

  const tabs = [
    {
      label: "Profile",
      key: "profile",
      children: (
        <UserForm
          onSubmit={onSubmit}
          initialValues={initialValues}
          {...props}
        />
      ),
    },
    {
      label: isRbacEnabled ? "Roles" : "Permissions",
      key: "roles",
      children: isRbacEnabled ? (
        <div className="w-full p-4 md:w-[70%] xl:w-3/5">
          <RolesForm />
        </div>
      ) : (
        <Flex style={{ gap: "97px" }}>
          <div className="w-full md:w-1/2 xl:w-1/2">
            <PermissionsForm />
          </div>
          <div
            className="absolute right-6 w-[35%] overflow-y-scroll border-l p-6"
            style={{ top: "96px", height: "calc(100% + 100px)" }}
          >
            <RoleDescriptionDrawer />
          </div>
        </Flex>
      ),
      disabled: rolesTabDisabled,
      forceRender: !rolesTabDisabled,
    },
  ];

  return <Tabs items={tabs} />;
};

export default UserManagementTabs;
