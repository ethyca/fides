import React, { ReactNode } from "react";

import Layout from "~/features/common/Layout";

type ConnectionLayoutProps = {
  children: ReactNode;
};

const ConnectionsLayout = ({ children }: ConnectionLayoutProps) => (
  <Layout title="Connections">{children}</Layout>
);

export default ConnectionsLayout;
