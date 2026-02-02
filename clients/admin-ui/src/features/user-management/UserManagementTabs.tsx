import { ChakraBox as Box, ChakraFlex as Flex, Tabs } from "fidesui";
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
  const isRbacEnabled = flags.rbacManagement;

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
        <Box w={{ base: "100%", md: "70%", xl: "60%" }} p={4}>
          <RolesForm />
        </Box>
      ) : (
        <Flex gap="97px">
          <Box w={{ base: "100%", md: "50%", xl: "50%" }}>
            <PermissionsForm />
          </Box>
          <Box
            position="absolute"
            top="96px"
            right={6}
            height="calc(100% + 100px)"
            overflowY="scroll"
            padding={6}
            w="35%"
            borderLeftWidth="1px"
          >
            <RoleDescriptionDrawer />
          </Box>
        </Flex>
      ),
      disabled: rolesTabDisabled,
      forceRender: !rolesTabDisabled,
    },
  ];

  return <Tabs items={tabs} />;
};

export default UserManagementTabs;
