import {Box, Flex} from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import DataTabs, { type TabData } from "~/features/common/DataTabs";

import PermissionsForm from "./PermissionsForm";
import { selectActiveUserId } from "./user-management.slice";
import UserForm, { type Props as UserFormProps } from "./UserForm";
import RoleDescriptionDrawer from "user-management/RoleDescriptionDrawer";
import {RoleRegistryEnum} from "~/types/api";

const UserManagementTabs = ({
  user,
  onSubmit,
  initialValues,
  ...props
}: UserFormProps) => {
  const activeUserId = useAppSelector(selectActiveUserId);

  const ROLES = [
    {
      label: "Owner",
      roleKey: RoleRegistryEnum.OWNER,
      description: "Owners have view and edit access to the whole organization and can create new users"
    },
    {
      label: "Contributor",
      roleKey: RoleRegistryEnum.CONTRIBUTOR,
      description: "Contributors can create new users and have view and edit access to the whole organization apart from configuring storage and messaging"
    },
    {
      label: "Viewer",
      roleKey: RoleRegistryEnum.VIEWER,
      description: "Viewers have view access to the Data Map and all systems"
    },
    {
      label: "Viewer & Approver",
      roleKey: RoleRegistryEnum.VIEWER_AND_APPROVER,
      description: "Viewer & Approvers have view access to the Data Map but can also manage Privacy Requests"
    },
    {
      label: "Approver",
      roleKey: RoleRegistryEnum.APPROVER,
      description: "Approvers can only access the Privacy Requests portal to manage requests"
    },
  ];

  const tabs: TabData[] = [
    {
      label: "Profile",
      content: (
        <UserForm
          user={user}
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
            <PermissionsForm roles={ROLES}/>
          </Box>
          <Box w={{ base: "100%", md: "35%", xl: "45%" }}>
            <RoleDescriptionDrawer roles={ROLES}/>
          </Box>
        </Flex>
      ),
      isDisabled: !activeUserId,
    },
  ];

  return <DataTabs data={tabs} />;
};

export default UserManagementTabs;
