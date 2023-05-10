import { Spinner } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useEffect } from "react";
import EditUserForm from "user-management/EditUserForm";
import {
  setActiveUserId,
  useGetUserByIdQuery,
} from "user-management/user-management.slice";
import UserManagementLayout from "user-management/UserManagementLayout";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

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
      <UserManagementLayout title="Edit User">
        <Spinner />
      </UserManagementLayout>
    );
  }

  if (existingUser == null) {
    return (
      <UserManagementLayout title="Edit User">
        Could not find profile ID.
      </UserManagementLayout>
    );
  }

  return (
    <UserManagementLayout title="Edit User">
      <EditUserForm user={existingUser} />
    </UserManagementLayout>
  );
};

export default Profile;
