import { Box, Heading } from '@fidesui/react';
import type { NextPage } from 'next';
import React from 'react';

import ProtectedRoute from '../../features/auth/ProtectedRoute';
import Head from '../../features/common/Head'
import NavBar from '../../features/common/NavBar';
import UserManagementTable from '../../features/user-management/UserManagementTable';
import UserManagementTableActions from '../../features/user-management/UserManagementTableActions';

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
