import { utf8ToB64 } from "common/utils";
import { useRouter } from "next/router";
import React, { useEffect } from "react";
import UserManagementTabs from "user-management/UserManagementTabs";

import { useAppDispatch } from "~/app/hooks";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

import {
  setActiveUserId,
  useCreateUserMutation,
} from "./user-management.slice";
import { FormValues } from "./UserForm";

const NewUserForm = () => {
  const router = useRouter();
  const [createUser] = useCreateUserMutation();
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(setActiveUserId(undefined));
  }, [dispatch]);

  const handleSubmit = async (values: FormValues) => {
    const b64Password = utf8ToB64(values.password);
    const result = await createUser({
      ...values,
      password: b64Password,
    }).unwrap();
    router.push(`${USER_MANAGEMENT_ROUTE}/profile/${result.id}`);
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
