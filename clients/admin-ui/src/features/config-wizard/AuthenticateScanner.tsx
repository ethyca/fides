import React from "react";

import { useAppSelector } from "~/app/hooks";
import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import AuthenticateRuntimeForm from "./AuthenticateRuntimeForm";
import { selectAddSystemsMethod } from "./config-wizard.slice";
import { SystemMethods } from "./types";

// TODO(#577)
const AuthenticateOktaForm = () => null;

const AuthenticateScanner = () => {
  const infrastructure = useAppSelector(selectAddSystemsMethod);
  return (
    <>
      {infrastructure === ValidTargets.AWS ? <AuthenticateAwsForm /> : null}
      {infrastructure === ValidTargets.OKTA ? <AuthenticateOktaForm /> : null}
      {infrastructure === SystemMethods.RUNTIME ? (
        <AuthenticateRuntimeForm />
      ) : null}
    </>
  );
};

export default AuthenticateScanner;
