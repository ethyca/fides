import React from "react";
import { useSelector } from "react-redux";
import UserManagementTabs from "user-management/UserManagementTabs";

import { selectUser } from "~/features/auth";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { USER_MANAGEMENT_ROUTE } from "../common/nav/routes";
import PageHeader from "../common/PageHeader";
import { User } from "./types";
import { useEditUserMutation } from "./user-management.slice";
import { FormValues } from "./UserForm";

const useUserForm = (profile: User) => {
  const currentUser = useSelector(selectUser);
  const [editUser] = useEditUserMutation();

  const initialValues: FormValues = {
    username: profile.username ?? "",
    email_address: profile.email_address ?? "",
    first_name: profile.first_name ?? "",
    last_name: profile.last_name ?? "",
    password: "",
    password_login_enabled: Boolean(profile.password_login_enabled),
  };

  const handleSubmit = async (values: FormValues) => {
    const userBody = {
      ...values,
      id: profile.id,
    };
    return editUser(userBody);
  };

  const isOwnProfile = currentUser ? currentUser.id === profile.id : false;
  const hasUserUpdatePermission = useHasPermission([
    ScopeRegistryEnum.USER_UPDATE,
  ]);
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
}
const EditUserForm = ({ user }: Props) => {
  const { handleSubmit, canUpdateUser, initialValues } = useUserForm(user);

  const canViewAllUsers = useHasPermission([ScopeRegistryEnum.USER_READ]);

  return (
    <div>
      <PageHeader
        heading="Users"
        breadcrumbItems={[
          {
            title: "All users",
            href: canViewAllUsers ? USER_MANAGEMENT_ROUTE : undefined,
          },
          { title: initialValues.username },
        ]}
      />
      <UserManagementTabs
        onSubmit={handleSubmit}
        initialValues={initialValues}
        canEditNames={canUpdateUser}
      />
    </div>
  );
};

export default EditUserForm;
