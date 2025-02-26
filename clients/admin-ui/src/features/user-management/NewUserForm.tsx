import { utf8ToB64 } from "common/utils";
import { useRouter } from "next/router";
import React, { useEffect } from "react";
import UserManagementTabs from "user-management/UserManagementTabs";

import { useAppDispatch } from "~/app/hooks";
import { isErrorResult } from "~/features/common/helpers";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";

import PageHeader from "../common/PageHeader";
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
    const b64Password = values.password
      ? utf8ToB64(values.password)
      : undefined;
    const result = await createUser({
      ...values,
      password: b64Password,
    });
    if (!isErrorResult(result)) {
      router.push(`${USER_MANAGEMENT_ROUTE}/profile/${result.data.id}`);
    }
    return result;
  };

  return (
    <div>
      <PageHeader
        heading="Users"
        breadcrumbItems={[
          {
            title: "All users",
            href: USER_MANAGEMENT_ROUTE,
          },
          { title: "New User" },
        ]}
      />
      <UserManagementTabs onSubmit={handleSubmit} />
    </div>
  );
};

export default NewUserForm;
