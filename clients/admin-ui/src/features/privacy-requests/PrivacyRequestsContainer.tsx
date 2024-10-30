import { Flex, Heading, Spacer } from "fidesui";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import { RequestTable } from "~/features/privacy-requests/RequestTable";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> },
);

const PrivacyRequestsContainer = () => {
  const { processing } = useDSRErrorAlert();

  const { plus: hasPlus } = useFeatures();

  useEffect(() => {
    processing();
  }, [processing]);

  return (
    <>
      <Flex data-testid="privacy-requests" gap={2}>
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Privacy Requests
        </Heading>
        <Spacer />
        {hasPlus && (
          <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_CREATE]}>
            <SubmitPrivacyRequest />
          </Restrict>
        )}
        <ActionButtons />
      </Flex>
      <RequestTable />
    </>
  );
};

export default PrivacyRequestsContainer;
