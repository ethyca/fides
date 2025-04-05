import { Box, Flex } from "fidesui";
import RoleDescriptionDrawer from "user-management/RoleDescriptionDrawer";

import { useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";
import { ScopeRegistryEnum } from "~/types/api";

import { useHasPermission } from "../common/Restrict";
import PermissionsForm from "./PermissionsForm";
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

  // Subscribe to active user
  useGetUserByIdQuery(activeUserId as string, { skip: !activeUserId });

  const canUpdateUserPermissions = useHasPermission([
    ScopeRegistryEnum.USER_PERMISSION_UPDATE,
  ]);

  // If it is a new user, or if the user does not have permission
  const permissionsTabDisabled = !activeUserId || !canUpdateUserPermissions;

  const tabs: TabData[] = [
    {
      label: "Profile",
      content: (
        <UserForm
          onSubmit={onSubmit}
          initialValues={initialValues}
          {...props}
        />
      ),
    },
    {
      label: "Permissions",
      content: (
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
      isDisabled: permissionsTabDisabled,
    },
  ];

  return <DataTabs data={tabs} />;
};

export default UserManagementTabs;
