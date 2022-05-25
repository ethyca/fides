// required import to teach TypeScript to pick up the types
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NextAuth from 'next-auth';

import { User as ClientUser } from '../features/user/types';

declare module 'next-auth' {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    accessToken: string;
    user: ClientUser;
  }

  interface User {
    token_data: {
      access_token: string;
    };

    user_data: {
      id: string;
      username: string;
      created_at: string;
      first_name: string;
      last_name: string;
    };
  }
}
