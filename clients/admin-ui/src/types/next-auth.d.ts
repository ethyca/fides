// required import to teach TypeScript to pick up the types
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NextAuth from "~/types/next-auth";

declare module "~/types/next-auth" {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    accessToken: string;
  }
}
