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
          <Box w={{ base: "100%", md: "50%", xl: "50%" }}>
            <PermissionsForm />
          </Box>
          <Box
            position="absolute"
            top="114px"
            right="24px"
            overflowY="scroll"
            padding="24px"
            w="35%"
            borderLeftWidth="1px"
            borderBottomWidth="1px"
          >
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
