import { Flex, Heading, Spacer } from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import RequestFilters from "privacy-requests/RequestFilters";
import RequestTable from "privacy-requests/RequestTable";
import { useEffect } from "react";

import Layout from "~/features/common/Layout";
import { useDSRErrorAlert } from "~/features/privacy-requests/hooks/useDSRErrorAlert";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const Home: NextPage = () => {
  const { processing } = useDSRErrorAlert();

  useEffect(() => {
    processing();
  }, [processing]);

  return (
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
};

export default Home;
