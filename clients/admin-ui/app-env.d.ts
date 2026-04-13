// React 19 no longer declares JSX as a global namespace.
// This re-exports it globally for compatibility with existing code.
interface ImportedJSX extends React.JSX.Element {}
declare namespace JSX {
  export type Element = React.JSX.Element;
  export type IntrinsicElements = React.JSX.IntrinsicElements;
  export type IntrinsicAttributes = React.JSX.IntrinsicAttributes;
  export type ElementChildrenAttribute = React.JSX.ElementChildrenAttribute;
}

declare module "process" {
  declare global {
    namespace NodeJS {
      interface ProcessEnv extends Dict<string> {
        /**
         * Next uses NODE_ENV for its own purposes. This has some downsides:
         *   - It will always always be "development" or "production" depending on
         *     the Next command used, regardless of actual environment variables.
         *   - This prevents the other common value "test" which is useful in Cypress.
         *
         * The community has gone with the workaround of "app env" for developer control:
         * https://github.com/vercel/next.js/discussions/25764
         */
        NEXT_PUBLIC_APP_ENV: typeof process.env.NODE_ENV;
      }
    }
  }
}
