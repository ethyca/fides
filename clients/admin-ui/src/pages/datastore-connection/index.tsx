import { Box } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import ProtectedRoute from "../../features/auth/ProtectedRoute";
import Head from "../../features/common/Head";
import NavBar from "../../features/common/NavBar";
import ConnectionFilters from "../../features/datastore-connections/ConnectionFilters";
import ConnectionGrid from "../../features/datastore-connections/ConnectionGrid";
import ConnectionHeading from "../../features/datastore-connections/ConnectionHeading";

const DatastoreConnections: NextPage = () => (
  <ProtectedRoute>
    <div>
      <Head />

      <NavBar />

      <main>
        <Box px={9} py={10}>
          <ConnectionHeading />
          <ConnectionFilters />
          <ConnectionGrid />
        </Box>
      </main>
    </div>
  </ProtectedRoute>
);
export default DatastoreConnections;
