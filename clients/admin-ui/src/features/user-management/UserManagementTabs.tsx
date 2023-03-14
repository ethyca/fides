import { Box, Flex } from "@fidesui/react";
import RoleDescriptionDrawer from "user-management/RoleDescriptionDrawer";

import { useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";

import PermissionsForm from "./PermissionsForm";
import {
  selectActiveUserId,
  useGetUserByIdQuery,
} from "./user-management.slice";
import UserForm, { type Props as UserFormProps } from "./UserForm";

const UserManagementTabs = ({
  onSubmit,
  initialValues,
  ...props
}: UserFormProps) => {
  const activeUserId = useAppSelector(selectActiveUserId);

  // Subscribe to active user
  useGetUserByIdQuery(activeUserId as string, { skip: !activeUserId });

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
          <Box w={{ base: "100%", md: "65%", xl: "55%" }}>
            <PermissionsForm />
          </Box>
          <Box w={{ base: "100%", md: "35%", xl: "45%" }}>
            <RoleDescriptionDrawer />
          </Box>
        </Flex>
      ),
      isDisabled: !activeUserId,
    },
  ];

  return <DataTabs data={tabs} />;
};

export default UserManagementTabs;
