import { Box, Heading } from "@fidesui/react";
import Head from "common/Head";
import NavBar from "common/NavBar";
import type { NextPage } from "next";
import React from "react";
import UserManagementTable from "user-management/UserManagementTable";
import UserManagementTableActions from "user-management/UserManagementTableActions";

import ProtectedRoute from "../../features/auth/ProtectedRoute";

const UserManagement: NextPage = () => (
  <ProtectedRoute>
    <div>
      <Head />

      <NavBar />

      <main>
        <Box px={9} py={10}>
          <Heading fontSize="2xl" fontWeight="semibold">
            User Management
          </Heading>
          <UserManagementTableActions />
          <UserManagementTable />
        </Box>
      </main>
    </div>
  </ProtectedRoute>
);

export default UserManagement;
