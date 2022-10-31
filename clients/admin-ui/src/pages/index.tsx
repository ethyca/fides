import { Flex, Heading, Spacer } from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import { LOGIN_ROUTE } from "~/constants";
import ProtectedRoute from "~/features/auth/ProtectedRoute";
import Layout from "~/features/common/Layout";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const Home: NextPage = () => (
  <ProtectedRoute redirectUrl={LOGIN_ROUTE}>
    <Layout title="Privacy Requests">
      <Flex>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Privacy Requests
        </Heading>
        <Spacer />
        <Flags
          authorizedFlags={["configureAlertsFlag"]}
          renderOn={() => <ActionButtons />}
        />
      </Flex>
      <RequestFilters />
      <RequestTable />
    </Layout>
  </ProtectedRoute>
);

export default Home;
