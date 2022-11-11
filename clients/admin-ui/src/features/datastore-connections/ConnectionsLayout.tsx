import React, { ReactNode } from "react";

import Layout from "~/features/common/Layout";

type ConnectionLayoutProps = {
  children: ReactNode;
};

const ConnectionsLayout: React.FC<ConnectionLayoutProps> = ({ children }) => (
  <Layout title="Connections">{children}</Layout>
);

export default ConnectionsLayout;
