# Adding a new Override Option to FidesJS

Follow the steps below, step by step. Do not change anything else, other than adding the provided new override. Changes should be very concise and targeted for the task at hand. Note: If an enum needs to be imported to support these steps, always import as a type to save on build sizes. If you are unable to locate the correct enum or interface to import, pause and let me add it for you.

1. Define and document the new option as part of the `FidesInitOptions` interface in FidesJS. This interface is found in [consent-types.ts](mdc:clients/fides-js/src/lib/consent-types.ts). Add your new option in camel-case and a small blurb above it describing briefly what it's for. This blurb is for the benefit of the FidesJS developer and is not published.

2. Now, we also need to include this new option in a list of options that can be used as an override. Include the option in the list of Picked properties in the FidesInitOptionsOverrides interface found in the same [consent-types.ts](mdc:clients/fides-js/src/lib/consent-types.ts) file.

3. Define and document the new option as part of the `FidesOptions` interface in FidesJS. This interface is found in [fides-options.ts](mdc:clients/fides-js/src/docs/fides-options.ts). Add your new option as snake-case in this instance (underscore separated). This interface serves both as public documentation as well as a consumable interface by the code-base. This documentation will be seen by the public so make it clear, concise, and descriptive. Watch for spelling and grammar errors. Be sure to show the default value.

4. Add the new option to the `FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP` which helps map the camel-case `FidesInitOptions` (name) to the snake case `FidesOptions` (key) and adds some security checks around types and validation. Ask me to double check each of these properties since debugging a mistake here can be quite elusive!

5. To support the new option as part of the `window.Fides` object, we need to add the option and its default to the options property where that object gets initialized. Update the return object of `getCoreFides` method in [init-utils.ts](mdc:clients/fides-js/src/lib/init-utils.ts).

6. To support testing, we need to add the default value to `mockOptions` in [automated-consent.test.ts](mdc:clients/fides-js/__tests__/lib/automated-consent.test.ts)

7. Before proceeding to the steps below, run a build of fides.js by running `npm run build` in the `clients/fides-js` directory in the terminal.

8. Enabling environment variable support happens in the Privacy Center. Start by adding the new option to the `PrivacyCenterSettings` interface. This interface is found in [PrivacyCenterSettings.ts](mdc:clients/privacy-center/app/server-utils/PrivacyCenterSettings.ts). Environment variables are always added using screaming snake-case (underscore separated in all caps) so we'll do that here, along with a small blurb to the right of it. This blurb is for the benefit of the Privacy Center developer and is not published.

9. We can now add the new option to the list of Environment Variables that gets loaded in to Privacy Center's settings. Add the new option to the `settings` constant of the `loadEnvironmentVariables` method found in [loadEnvironmentVariables.ts](mdc:clients/privacy-center/app/server-utils/loadEnvironmentVariables.ts). Ask me to double check how this gets loaded and how the default gets set. For example, keep in mind that environment variables are always strings and must be coerced into a boolean, etc.

10. Exposing the environment variable to the client requires updating the list of `Pick`ed properties of the `PrivacyCenterClientSettings` interface found in [server-environment.ts](mdc:clients/privacy-center/app/server-environment.ts)

11. Once that interface is updated, we can now update the `clientSettings` constant variable to include the new option. This is found in the same [server-environment.ts](mdc:clients/privacy-center/app/server-environment.ts) file.

12. Lastly, we need to expose the settings variable to the client. Update the `fidesConfig` constant in [fides-js.ts](mdc:clients/privacy-center/pages/api/fides-js.ts) to include the new option.

13. Now is a good time to build the Privacy Center to ensure there are no unexpected errors. Run `npm run build` from the `clients/privacy-center` directory in the terminal.
