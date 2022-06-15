import { Box, Heading } from "@fidesui/react";
import type { NextPage } from "next";

import ProtectedRoute from "../features/auth/ProtectedRoute";
import Head from "../features/common/Head";
import NavBar from "../features/common/NavBar";
import RequestFilters from "../features/privacy-requests/RequestFilters";
import RequestTable from "../features/privacy-requests/RequestTable";

const Home: NextPage = () => (
  <ProtectedRoute redirectUrl="/login">
    <>
      <Head />
      <NavBar />

      <main>
        <Box px={9} py={10}>
          <Heading mb={8} fontSize="2xl" fontWeight="semibold">
            Subject Requests
          </Heading>
          <RequestFilters />
          <RequestTable />
        </Box>
      </main>
    </>
  </ProtectedRoute>
);

export default Home;
