import { utf8ToB64 } from "common/utils";
import React, { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";

import {
  setActiveUserId,
  useCreateUserMutation,
} from "./user-management.slice";
import { FormValues } from "./UserForm";
import UserManagementTabs from "./UserManagementTabs";

const NewUserForm = () => {
  const [createUser] = useCreateUserMutation();
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(setActiveUserId(undefined));
  }, [dispatch]);

  const handleSubmit = (values: FormValues) => {
    const b64Password = utf8ToB64(values.password);
    return createUser({ ...values, password: b64Password });
  };

  return (
    <div>
      <main>
        <UserManagementTabs onSubmit={handleSubmit} />
      </main>
    </div>
  );
};

export default NewUserForm;
