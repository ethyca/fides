import { Flex, Heading, Spacer } from "@fidesui/react";
import type { NextPage } from "next";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";

import Layout from "~/features/common/Layout";
import ActionButtons from "~/features/privacy-requests/buttons/ActionButtons";

const Home: NextPage = () => (
  <Layout title="Privacy Requests">
    <Flex>
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Privacy Requests
      </Heading>
      <Spacer />
      <ActionButtons />
    </Flex>
    <RequestFilters />
    <RequestTable />
  </Layout>
);

export default Home;
