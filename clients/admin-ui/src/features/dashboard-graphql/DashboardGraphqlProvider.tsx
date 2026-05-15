import { ApolloProvider } from "@apollo/client";
import { type ReactNode, useMemo } from "react";

import { createApolloClient } from "./apolloClient";

export const DashboardGraphqlProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const client = useMemo(() => createApolloClient(), []);
  return <ApolloProvider client={client}>{children}</ApolloProvider>;
};
