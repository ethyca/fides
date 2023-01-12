import { Flex, Heading, Spacer } from "@fidesui/react";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect } from "react";

import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";
import RequestFilters from "./RequestFilters";
import RequestTable from "./RequestTable";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const PrivacyRequestsContainer: React.FC = () => {
  const { processing } = useDSRErrorAlert();

  useEffect(() => {
    processing();
  }, [processing]);

  return (
    <>
      <Flex>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Privacy Requests
        </Heading>
        <Spacer />
        <ActionButtons />
      </Flex>
      <RequestFilters />
      <RequestTable />
    </>
  );
};

export default PrivacyRequestsContainer;
