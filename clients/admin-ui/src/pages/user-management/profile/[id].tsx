import { Spinner } from "@fidesui/react";
import { useRouter } from "next/router";
import React, { useEffect } from "react";
import EditUserForm from "user-management/EditUserForm";
import {
  setActiveUserId,
  useGetUserByIdQuery,
} from "user-management/user-management.slice";
import UserManagementLayout from "user-management/UserManagementLayout";

import { useAppDispatch } from "~/app/hooks";

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

  useEffect(() => {
    if (existingUser) {
      dispatch(setActiveUserId(existingUser.id));
    }
  }, [dispatch, existingUser]);

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
