import { Spinner } from "fidesui";
import { useRouter } from "next/router";
import React, { ReactNode, useEffect } from "react";
import EditUserForm from "user-management/EditUserForm";
import {
  setActiveUserId,
  useGetUserByIdQuery,
} from "user-management/user-management.slice";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import Layout from "~/features/common/Layout";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

const UserManagementLayout = ({ children }: { children: ReactNode }) => (
  <Layout title="Users">{children}</Layout>
);

const Profile = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  let profileId = "";
  if (router.query.id) {
    profileId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  } else {
    profileId = "";
  }
  const { data: existingUser, isLoading: isLoadingUser } =
    useGetUserByIdQuery(profileId);

  // Must have edit user permission or be the user's profile
  const loggedInUser = useAppSelector(selectUser);
  const isOwnProfile =
    loggedInUser && existingUser ? loggedInUser.id === existingUser.id : false;
  const canAccess =
    useHasPermission([ScopeRegistryEnum.USER_UPDATE]) || isOwnProfile;

  useEffect(() => {
    if (existingUser) {
      dispatch(setActiveUserId(existingUser.id));
    }
  }, [dispatch, existingUser, canAccess]);

  // Redirect to the home page if the user should not be able to access this page
  useEffect(() => {
    if (existingUser && !canAccess) {
      router.push("/");
    }
  }, [router, canAccess, existingUser]);

  if (isLoadingUser) {
    return (
      <UserManagementLayout>
        <Spinner />
      </UserManagementLayout>
    );
  }

  if (existingUser == null) {
    return (
      <UserManagementLayout>Could not find profile ID.</UserManagementLayout>
    );
  }

  return (
    <UserManagementLayout>
      <EditUserForm user={existingUser} />
    </UserManagementLayout>
  );
};

export default Profile;
