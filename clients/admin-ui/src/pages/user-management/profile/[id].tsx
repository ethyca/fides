import React from 'react';
import type { NextPage } from 'next';
import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
} from '@fidesui/react';

import NavBar from '../../../features/common/NavBar';
import EditUserForm from '../../../features/user-management/EditUserForm';
import {
  assignToken,
  setUser,
  userApi,
} from '../../../features/user/user.slice';
import { User } from '../../../features/user/types';
import { wrapper } from '../../../app/store';
import { getSession } from 'next-auth/react';

const Profile: NextPage<{ session: { user: User } }> = ({ session }) => {
  return (
    <div>
      <NavBar />
      <main>
        <Box px={9} py={10}>
          <Heading fontSize="2xl" fontWeight="semibold">
            User Management
            <Box mt={2} mb={7}>
              <Breadcrumb fontWeight="medium" fontSize="sm">
                <BreadcrumbItem>
                  <BreadcrumbLink href="/user-management">
                    User Management
                  </BreadcrumbLink>
                </BreadcrumbItem>

                <BreadcrumbItem>
                  <BreadcrumbLink href="#">Edit User</BreadcrumbLink>
                </BreadcrumbItem>
              </Breadcrumb>
            </Box>
          </Heading>
          {/* @ts-ignore */}
          <EditUserForm user={session.user} />
        </Box>
      </main>
    </div>
  );
};

export default Profile;

export const getServerSideProps = wrapper.getServerSideProps(
  (store) => async (context) => {
    const session = await getSession(context);
    if (session && typeof session.accessToken !== 'undefined') {
      await store.dispatch(assignToken(session.accessToken));
      await store.dispatch(setUser(session.user));

      if (context.query.id) {
        store.dispatch(
          userApi.endpoints.getUserById.initiate(context.query.id as string)
        );
        store.dispatch(
          userApi.endpoints.getUserPermissions.initiate(
            context.query.id as string
          )
        );
        await Promise.all(userApi.util.getRunningOperationPromises());
      }
      return { props: { session, query: context.query } };
    }

    return {
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }
);
