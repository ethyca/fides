import { useAppSelector } from "~/app/hooks";
import { ValidTargets } from "~/types/api";

import AuthenticateAwsForm from "./AuthenticateAwsForm";
import AuthenticateOktaForm from "./AuthenticateOktaForm";
import { selectAddSystemsMethod } from "./config-wizard.slice";

const AuthenticateScanner = () => {
  const infrastructure = useAppSelector(selectAddSystemsMethod);
  return (
    <>
      {infrastructure === ValidTargets.AWS && <AuthenticateAwsForm />}
      {infrastructure === ValidTargets.OKTA && <AuthenticateOktaForm />}
    </>
  );
};

export default AuthenticateScanner;
