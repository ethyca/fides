import { commonPasswords, PasswordStrength } from "tai-password-strength";
import * as Yup from "yup";

export const passwordValidation = Yup.string()
  .required()
  .min(8, "Password must have at least eight characters.")
  .matches(/[0-9]/, "Password must have at least one number.")
  .matches(/[A-Z]/, "Password must have at least one capital letter.")
  .matches(/[a-z]/, "Password must have at least one lowercase letter.")
  .matches(/[\W_]/, "Password must have at least one symbol.")
  .test(
    "is-common-password",
    "Password cannot be a common password.",
    passwordIsNotCommon,
  );

function passwordIsNotCommon(password: string) {
  const strengthTester = new PasswordStrength();
  const strength = strengthTester
    .addCommonPasswords(commonPasswords)
    .check(password);
  return !strength.commonPassword;
}
