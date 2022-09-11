import React from "react";
import NewUserForm from "user-management/NewUserForm";
import UserManagementLayout from "user-management/UserManagementLayout";

const CreateNewUser = () => (
  <UserManagementLayout title="New User">
    <NewUserForm />
  </UserManagementLayout>
);

export default CreateNewUser;
