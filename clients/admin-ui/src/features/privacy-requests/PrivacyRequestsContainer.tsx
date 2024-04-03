import { Flex, Heading, Spacer } from "@fidesui/react";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";
import RequestFilters from "./RequestFilters";
import RequestTable from "./RequestTable";

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
        {hasPlus ? (
          <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_CREATE]}>
            <SubmitPrivacyRequest />
          </Restrict>
        ) : null}
        <ActionButtons />
      </Flex>
      <RequestFilters revealPII={revealPII} setRevealPII={setRevealPII} />
      <RequestTable revealPII={revealPII} />
    </>
  );
};

export default PrivacyRequestsContainer;
