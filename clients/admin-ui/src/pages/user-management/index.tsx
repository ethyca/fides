import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";
import UserManagementTableActions from "user-management/UserManagementTableActions";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const UserManagement: NextPage = () => (
  <Layout title="User Management">
    <PageHeader
      heading="Users"
      breadcrumbItems={[
        {
          title: "All users",
        },
      ]}
    />
    <UserManagementTableActions />
    <UserManagementTable />
  </Layout>
);

export default UserManagement;
