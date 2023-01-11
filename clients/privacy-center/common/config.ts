/* eslint-disable import/prefer-default-export */
import { config } from "~/constants";

interface ValidityMessage {
  isValid: boolean;
  message?: string;
}

/**
 * We can catch business logic problems with the supplied config.json here.
 *
 * Typescript errors will be caught by the initial instantiation of the config object.
 */
export const configIsValid = (): ValidityMessage => {
  // Cannot currently have more than one consent be executable
  if (config.consent) {
    const executables = config.consent.consentOptions.filter(
      (option) => option.executable
    );
    if (executables.length > 1) {
      return {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      };
    }
  }
  return { isValid: true };
};
