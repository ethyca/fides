import {
  ApolloClient,
  createHttpLink,
  InMemoryCache,
  type NormalizedCacheObject,
} from "@apollo/client";
import { setContext } from "@apollo/client/link/context";

import { addCommonHeaders } from "~/features/common/CommonHeaders";

// The Strawberry endpoint is mounted at the app root (/graphql), NOT under
// the /api/v1 prefix that NEXT_PUBLIC_FIDESCTL_API points at. Post to the
// relative /graphql path: in dev the Next rewrite proxies it to the backend,
// and in mock mode MSW intercepts it.
const httpLink = createHttpLink({
  uri: "/graphql",
});

/**
 * Reads the auth token from the redux store and folds in the same headers
 * applied to RTK Query requests via addCommonHeaders.
 *
 * Redux is imported lazily to avoid a circular dependency between the
 * Apollo client setup (which has to run early in _app.tsx) and the store.
 */
const authLink = setContext(async (_, { headers }) => {
  const { default: store } = await import("~/app/store");
  const { token } = store.getState().auth;
  const next = new Headers(headers as HeadersInit);
  addCommonHeaders(next, token);
  return { headers: Object.fromEntries(next.entries()) };
});

export const createApolloClient = (): ApolloClient<NormalizedCacheObject> =>
  new ApolloClient({
    link: authLink.concat(httpLink),
    cache: new InMemoryCache(),
    connectToDevTools: process.env.NODE_ENV !== "production",
  });
