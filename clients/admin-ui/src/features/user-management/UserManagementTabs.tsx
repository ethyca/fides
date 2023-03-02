import { Box } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";

import PermissionsForm from "./PermissionsForm";
import { selectActiveUserId } from "./user-management.slice";
import UserForm, { type Props as UserFormProps } from "./UserForm";

const UserManagementTabs = ({
  onSubmit,
  initialValues,
  ...props
}: UserFormProps) => {
  const activeUserId = useAppSelector(selectActiveUserId);

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
        <Box w={{ base: "100%", md: "65%", xl: "50%" }}>
          <PermissionsForm />
        </Box>
      ),
      isDisabled: !activeUserId,
    },
  ];

  return <DataTabs data={tabs} />;
};

export default UserManagementTabs;
