/**
 * We can catch business logic problems with the supplied config.json here.
 *
 * Typescript errors will be caught by the initial instantiation of the config object.
 */
const configIsValid = (
  /** @type {import('~/types/config').Config} */
  config
) => {
  // Cannot currently have more than one consent be executable
  if (config.consent) {
    const executables = config.consent.page.consentOptions.filter(
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

/**
 * Loads `config.json`, validates it, and throws an exception if it is invalid.
 */
const validateConfig = () => {
  const privacyCenterConfig = require("../config/config.json");
  const { isValid, message } = configIsValid(privacyCenterConfig);
  if (!isValid) {
    // Throw a red warning
    console.error(
      "\x1b[31m%s",
      `Error with privacy center configuration: ${message}`
    );
    throw "Privacy center config invalid. Please fix, then rerun the application.";
  }
};

module.exports = {
  configIsValid,
  validateConfig,
};
