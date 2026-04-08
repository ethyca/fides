import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { SidePanel } from "~/features/common/SidePanel";
import useUserManagementTable from "~/features/user-management/useUserManagementTable";

const UserManagement: NextPage = () => {
  const { error } = useUserManagementTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching user management"
      />
    );
  }
  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Users"
          breadcrumbItems={[{ title: "All users" }]}
        />
      </SidePanel>
      <FixedLayout title="User Management">
        <UserManagementTable />
      </FixedLayout>
    </>
  );
};

export default UserManagement;
