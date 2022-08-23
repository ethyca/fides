import { Divider, Heading } from "@fidesui/react";
import React from "react";

import { utf8ToB64 } from "../common/utils";
import { useCreateUserMutation } from "./user-management.slice";
import UserForm, { FormValues } from "./UserForm";

const NewUserForm = () => {
  const [createUser] = useCreateUserMutation();

  const handleSubmit = (values: FormValues) => {
    const b64Password = utf8ToB64(values.password);
    return createUser({ ...values, password: b64Password });
  };

  return (
    <div>
      <main>
        <Heading mb={4} fontSize="xl" colorScheme="primary">
          Profile
        </Heading>
        <Divider mb={7} />
        <UserForm onSubmit={handleSubmit} />
      </main>
    </div>
  );
};

export default NewUserForm;
