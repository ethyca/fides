import { Heading } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";
import UserManagementTableActions from "user-management/UserManagementTableActions";

import Layout from "~/features/common/Layout";

const UserManagement: NextPage = () => (
  <Layout title="User Management">
    <Heading fontSize="2xl" fontWeight="semibold" mb={4}>
      User Management
    </Heading>
    <UserManagementTableActions />
    <UserManagementTable />
  </Layout>
);

export default UserManagement;
