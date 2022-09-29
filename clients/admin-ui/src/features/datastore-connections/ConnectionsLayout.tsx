import React, { ReactNode } from "react";

import Layout from "~/features/common/Layout";

import ProtectedRoute from "../auth/ProtectedRoute";

type ConnectionLayoutProps = {
  children: ReactNode;
};

const ConnectionsLayout: React.FC<ConnectionLayoutProps> = ({ children }) => (
  <ProtectedRoute>
    <Layout title="Datastore Connections">{children}</Layout>
  </ProtectedRoute>
);

export default ConnectionsLayout;
