import { Heading } from "@fidesui/react";
import type { NextPage } from "next";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";

import { LOGIN_ROUTE } from "~/constants";
import ProtectedRoute from "~/features/auth/ProtectedRoute";
import Layout from "~/features/common/Layout";

const Home: NextPage = () => (
  <ProtectedRoute redirectUrl={LOGIN_ROUTE}>
    <Layout title="Subject Requests">
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Subject Requests
      </Heading>
      <RequestFilters />
      <RequestTable />
    </Layout>
  </ProtectedRoute>
);

export default Home;
