import React from "react";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import { Infrastructure } from "./types";

// TODO(#577)
const AuthenticateOktaForm = () => null;

interface Props {
  infrastructure?: Infrastructure;
}

const AuthenticateScanner = ({ infrastructure = "aws" }: Props) => (
  <>
    {infrastructure === "aws" ? <AuthenticateAwsForm /> : null}
    {infrastructure === "okta" ? <AuthenticateOktaForm /> : null}
  </>
);

export default AuthenticateScanner;
