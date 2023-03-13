import { utf8ToB64 } from "common/utils";
import { router } from "next/client";
import React, { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/constants";

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
    createUser({ ...values, password: b64Password });
    router.push(`${USER_MANAGEMENT_ROUTE}`);
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
