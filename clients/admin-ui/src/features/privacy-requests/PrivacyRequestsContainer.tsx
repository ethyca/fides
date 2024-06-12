import { Flex, Heading, Spacer } from "fidesui";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import { RequestTable } from "~/features/privacy-requests/RequestTable";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import DeprecatedRequestFilters from "./DeprecatedRequestFilters";
import DeprecatedRequestTable from "./DeprecatedRequestTable";
import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> }
);

const PrivacyRequestsContainer: React.FC = () => {
  const { processing } = useDSRErrorAlert();
  const [revealPII, setRevealPII] = useState(false);

  const { plus: hasPlus } = useFeatures();

  useEffect(() => {
    processing();
  }, [processing]);

  return (
    <>
      <Flex data-testid="privacy-requests" gap={4}>
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
      <DeprecatedRequestFilters
        revealPII={revealPII}
        setRevealPII={setRevealPII}
      />
      <DeprecatedRequestTable revealPII={revealPII} />
    </>
  );
};

export default PrivacyRequestsContainer;
