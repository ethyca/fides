import React from "react";

import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";

// TODO(#577)
const AuthenticateOktaForm = () => null;

interface Props {
  infrastructure?: ValidTargets;
}

const AuthenticateScanner = ({ infrastructure = ValidTargets.AWS }: Props) => (
  <>
    {infrastructure === ValidTargets.AWS ? <AuthenticateAwsForm /> : null}
    {infrastructure === ValidTargets.OKTA ? <AuthenticateOktaForm /> : null}
  </>
);

export default AuthenticateScanner;
