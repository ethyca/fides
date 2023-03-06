import { Divider, Heading } from "@fidesui/react";
import React from "react";
import { useSelector } from "react-redux";

import { selectUser } from "~/features/auth";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistry } from "~/types/api";

import { User, UserPermissions } from "./types";
import { useEditUserMutation } from "./user-management.slice";
import UserForm, { FormValues } from "./UserForm";

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
  const hasUserUpdatePermission = useHasPermission([ScopeRegistry.USER_UPDATE]);
  const canUpdateUser = isOwnProfile ? true : hasUserUpdatePermission;

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
        <Heading mb={4} fontSize="xl" colorScheme="primary">
          Profile
        </Heading>
        <Divider mb={7} />
        <UserForm
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
