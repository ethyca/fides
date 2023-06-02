import { UseToastOptions } from "@chakra-ui/react";

const BaseToastOptions: UseToastOptions = {
  position: "top",
  duration: 5500,
};

export const ErrorToastOptions: UseToastOptions = {
  status: "error",
  ...BaseToastOptions,
};

export const ConfigErrorToastOptions: UseToastOptions = {
  title: "An error occurred while retrieving the Privacy Center Config",
  ...ErrorToastOptions,
};

export const SuccessToastOptions: UseToastOptions = {
  status: "success",
  ...BaseToastOptions,
};
