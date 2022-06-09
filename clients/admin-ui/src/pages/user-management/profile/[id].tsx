import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
} from '@fidesui/react';
import type { NextPage } from 'next';
import Link from 'next/link';
import React from 'react';

import ProtectedRoute from '../../../features/auth/ProtectedRoute';
import NavBar from '../../../features/common/NavBar';
import EditUserForm from '../../../features/user-management/EditUserForm';

const Profile: NextPage = () => (
  <ProtectedRoute>
    <div>
      <NavBar />
      <main>
        <Box px={9} py={10}>
          <Heading fontSize="2xl" fontWeight="semibold">
            User Management
            <Box mt={2} mb={7}>
              <Breadcrumb fontWeight="medium" fontSize="sm">
                <BreadcrumbItem>
                  <Link href="/user-management" passHref>
                    <BreadcrumbLink href="/user-management">
                      User Management
                    </BreadcrumbLink>
                  </Link>
                </BreadcrumbItem>

                <BreadcrumbItem>
                  <BreadcrumbLink href="#">Edit User</BreadcrumbLink>
                </BreadcrumbItem>
              </Breadcrumb>
            </Box>
          </Heading>
          <EditUserForm />
        </Box>
      </main>
    </div>
  </ProtectedRoute>
);

export default Profile;
