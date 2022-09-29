import { Heading } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";
import UserManagementTableActions from "user-management/UserManagementTableActions";

import ProtectedRoute from "~/features/auth/ProtectedRoute";
import Layout from "~/features/common/Layout";

const UserManagement: NextPage = () => (
  <ProtectedRoute>
    <Layout title="User Management">
      <Heading fontSize="2xl" fontWeight="semibold">
        User Management
      </Heading>
      <UserManagementTableActions />
      <UserManagementTable />
    </Layout>
  </ProtectedRoute>
);

export default UserManagement;
