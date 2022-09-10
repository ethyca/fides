import { Box } from "@fidesui/react";
import Head from "common/Head";
import NavBar from "common/NavBar";
import React, { ReactNode } from "react";

import ProtectedRoute from "../auth/ProtectedRoute";

type ConnectionLayoutProps = {
  children: ReactNode;
};

const ConnectionsLayout: React.FC<ConnectionLayoutProps> = ({ children }) => (
  <ProtectedRoute>
    <>
      <Head />
      <NavBar />
      <main>
        <Box px={9} py={10}>
          {children}
        </Box>
      </main>
    </>
  </ProtectedRoute>
);

export default ConnectionsLayout;
