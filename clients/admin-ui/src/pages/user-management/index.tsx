import { Box, Heading } from '@fidesui/react';
import type { NextPage } from 'next';
import Head from 'next/head';
import React from 'react';

import ProtectedRoute from '../../features/auth/ProtectedRoute';
import NavBar from '../../features/common/NavBar';
import UserManagementTable from '../../features/user-management/UserManagementTable';
import UserManagementTableActions from '../../features/user-management/UserManagementTableActions';

const UserManagement: NextPage = () => (
  <ProtectedRoute>
    <div>
      <Head>
        <title>Fides Admin UI - User Management</title>
        <meta name="description" content="Generated from FidesUI template" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

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
