import React from "react";

import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import AuthenticateRuntimeForm from "./AuthenticateRuntimeForm";
import { AddSystemMethods, SystemMethods } from "./types";

// TODO(#577)
const AuthenticateOktaForm = () => null;

interface Props {
  infrastructure?: AddSystemMethods;
}

const AuthenticateScanner = ({ infrastructure = ValidTargets.AWS }: Props) => (
  <>
    {infrastructure === ValidTargets.AWS ? <AuthenticateAwsForm /> : null}
    {infrastructure === ValidTargets.OKTA ? <AuthenticateOktaForm /> : null}
    {infrastructure === SystemMethods.RUNTIME ? (
      <AuthenticateRuntimeForm />
    ) : null}
  </>
);

export default AuthenticateScanner;
