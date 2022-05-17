import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

export default NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: {
          label: 'Email',
          type: 'text',
          placeholder: 'username',
        },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        let res;

        try {
          res = await fetch(`${process.env.NEXT_PUBLIC_FIDESOPS_API!}/login`, {
            method: 'POST',
            body: JSON.stringify({
              username: credentials!.email,
              password: credentials!.password,
            }),
            headers: { 'Content-Type': 'application/json' },
          });
        } catch (error) {
          throw new Error('Failed to authenticate');
        }

        if (!res || !res.ok) {
          throw new Error('Failed to authenticate');
        }

        const user = await res.json();

        // If no error and we have user data, return it
        if (res.ok && user) {
          return user;
        }

        // Return null if user data could not be retrieved
        return null;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user?.token_data?.access_token) {
        Object.assign(token, {
          token: user.token_data.access_token,
          user: user.user_data,
        });
      }

      return token;
    },
    async session({ session, token }) {
      Object.assign(session, {
        accessToken: token.token,
        user: token.user,
      });
      return session;
    },
  },
});
