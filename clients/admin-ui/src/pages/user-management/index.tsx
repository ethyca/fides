import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
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
    <FixedLayout title="User Management">
      <PageHeader
        heading="Users"
        breadcrumbItems={[
          {
            title: "All users",
          },
        ]}
        isSticky={false}
      />
      <UserManagementTable />
    </FixedLayout>
  );
};

export default UserManagement;
