import * as Yup from "yup";

export const passwordValidation = Yup.string()
  .required()
  .min(8, "Password must have at least eight characters.")
  .matches(/[0-9]/, "Password must have at least one number.")
  .matches(/[A-Z]/, "Password must have at least one capital letter.")
  .matches(/[a-z]/, "Password must have at least one lowercase letter.")
  .matches(/[\W]/, "Password must have at least one symbol.");
