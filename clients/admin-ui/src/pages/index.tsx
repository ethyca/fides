import { Flex, Heading, Spacer } from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";

import { LOGIN_ROUTE } from "~/constants";
import ProtectedRoute from "~/features/auth/ProtectedRoute";
import Layout from "~/features/common/Layout";
import ActionButtons from "~/features/privacy-requests/buttons/ActionButtons";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const Home: NextPage = () => (
  <ProtectedRoute redirectUrl={LOGIN_ROUTE}>
    <Layout title="Subject Requests">
      <Flex>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Subject Requests
        </Heading>
        <Spacer />
        <ActionButtons />
      </Flex>
      <RequestFilters />
      <RequestTable />
    </Layout>
  </ProtectedRoute>
);

export default Home;
