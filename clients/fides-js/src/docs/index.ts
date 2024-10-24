/**
 * FidesJS is a JavaScript SDK to integrate Fides consent into any website or
 * app! Commonly referred to as a Consent Management Platform (CMP), FidesJS
 * includes all the UI components (banners, modals, etc.), state management, and
 * utility functions you need to collect consent & enforce data privacy in your
 * application.
 *
 * For example, FidesJS is used to:
 * - automatically configure the current user session with the applicable
 * default consent preferences for their location (e.g. opt-out of data sales,
 * opt-in to analytics, etc.)
 * - show a consent UI component (banner, modal, etc.) to the current user with
 * the applicable privacy notices for them to opt-in, opt-out, etc.
 * - store the current user's consent preferences in a first-party cookie to
 * remember their choices in future sessions
 * - expose the current user's consent preferences via a simple `Fides.consent`
 * JavaScript API to integrate consent into your own application
 * - dispatch events on the global `window` (e.g. `FidesUpdated`,
 * `FidesUIShown`) to easily sync consent changes to your application in
 * real-time based on the current user's actions
 * - integrate the current user's consent to other scripts via integrations with
 * Google Tag Manager, IAB TCF, etc.
 * - ...and more!
 *
 * See {@link Fides} for how to use the `window.Fides` JavaScript API, {@link
 * FidesOptions} for supported options to customize it's behavior, and {@link
 * FidesEvent} for how to use `window.addEventListener(...)` to subscribe to
 * custom Fides events for real-time updates.
 *
 * @packageDocumentation
 */

/**
 * NOTE: This src/docs directory defines a subset of types used by this project
 * that should be the user-facing classes, functions, events, etc. that
 * engineers integrating FidesJS into their own applications rely on. The TSDoc
 * comments are then used to generate (via `npm run docs:generate`) living
 * developer documentation that is then imported and hosted on Ethyca's
 * docs site here: [FidesJS SDK Documentation](https://ethyca.com/docs/dev-docs/js)
 *
 * Therefore, all the types in src/docs should be considered part of FidesJS'
 * *official* developer API, so treat them with care!
 *
 * You can also use the "internal" tag to intentionally leave specific
 * properties/comments/etc. undocumented; this can be useful for internal-only
 * types for developers contributing directly to FidesJS, but that shouldn't be
 * included in the generic developer documentation.
 */

// Export all the types from files in src/docs directory
export * from "./fides";
export * from "./fides-event";
export * from "./fides-experience-config";
export * from "./fides-options";
