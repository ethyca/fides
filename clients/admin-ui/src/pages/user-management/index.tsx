import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";

const UserManagement: NextPage = () => (
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

export default UserManagement;
