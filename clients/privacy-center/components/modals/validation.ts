import dayjs from "dayjs";
import * as Yup from "yup";

import { CustomDateField } from "~/types/config";

export const dateFieldValidation = (
  field: Pick<CustomDateField, "min" | "max">,
  label: string,
  isRequired: boolean,
) => {
  let schema = Yup.string().test(
    "valid-date",
    `${label} must be a valid date (MM/DD/YYYY)`,
    (v) => !v || dayjs(v, "YYYY-MM-DD", true).isValid(),
  );
  if (field.max) {
    schema = schema.test(
      "not-after-max",
      `${label} must be on or before ${field.max}`,
      (v) => !v || v <= field.max!,
    );
  }
  if (field.min) {
    schema = schema.test(
      "not-before-min",
      `${label} must be on or after ${field.min}`,
      (v) => !v || v >= field.min!,
    );
  }
  return isRequired ? schema.required(`${label} is required`) : schema;
};

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
