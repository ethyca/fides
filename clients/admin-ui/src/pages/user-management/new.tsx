import React from "react";

import NewUserForm from "../../features/user-management/NewUserForm";
import UserManagementLayout from "../../features/user-management/UserManagementLayout";

const CreateNewUser = () => (
  <UserManagementLayout title="New User">
    <NewUserForm />
  </UserManagementLayout>
);

export default CreateNewUser;
