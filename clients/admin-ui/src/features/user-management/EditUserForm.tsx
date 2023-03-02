import React from "react";
import { useSelector } from "react-redux";

import { selectUser } from "../auth";
import { User, UserPermissions } from "./types";
import {
  useEditUserMutation,
  useGetUserPermissionsQuery,
} from "./user-management.slice";
import { FormValues } from "./UserForm";
import UserManagementTabs from "./UserManagementTabs";

const useUserForm = (profile: User, permissions: UserPermissions) => {
  const currentUser = useSelector(selectUser);
  const [editUser] = useEditUserMutation();

  const initialValues = {
    username: profile.username ?? "",
    first_name: profile.first_name ?? "",
    last_name: profile.last_name ?? "",
    password: "",
    scopes: permissions.scopes ?? [],
    id: profile.id,
  };

  const handleSubmit = async (values: FormValues) => {
    const userBody = { ...profile, ...values };
    return editUser(userBody);
  };

  const isOwnProfile = currentUser ? currentUser.id === profile.id : false;

  let canUpdateUser = false;
  const { data: userPermissions } = useGetUserPermissionsQuery(
    currentUser?.id ?? ""
  );
  if (isOwnProfile) {
    canUpdateUser = true;
  } else {
    canUpdateUser = userPermissions
      ? userPermissions.scopes.includes("user:update")
      : false;
  }

  return {
    handleSubmit,
    isOwnProfile,
    canUpdateUser,
    initialValues,
  };
};

interface Props {
  user: User;
  permissions: UserPermissions;
}
const EditUserForm = ({ user, permissions }: Props) => {
  const { isOwnProfile, handleSubmit, canUpdateUser, initialValues } =
    useUserForm(user, permissions);

  return (
    <div>
      <main>
        <UserManagementTabs
          onSubmit={handleSubmit}
          initialValues={initialValues}
          canEditNames={canUpdateUser}
          canChangePassword={isOwnProfile}
        />
      </main>
    </div>
  );
};

export default EditUserForm;
