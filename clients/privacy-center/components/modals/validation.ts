import * as Yup from "yup";

export const nameValidation = (option?: string | null) => {
  let validation = Yup.string();
  if (option === "required") {
    validation = validation.required("Name is required");
  } else {
    validation = validation.optional();
  }
  return validation;
};

export const emailValidation = (option?: string | null) => {
  let validation = Yup.string().email("Email is invalid");
  if (option === "required") {
    validation = validation.required("Email is required");
  } else {
    validation = validation.optional();
  }
  return validation;
};

export const phoneValidation = (option?: string | null) => {
  // E.164 international standard format
  let validation = Yup.string().matches(
    /^\+[1-9]\d{1,14}$/,
    "Phone is invalid",
  );
  if (option === "required") {
    validation = validation.required("Phone is required");
  } else {
    validation = validation.optional();
  }
  return validation;
};
