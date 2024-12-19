import { AntSpace as Space } from "fidesui";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import { RequestTable } from "~/features/privacy-requests/RequestTable";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import PageHeader from "../common/PageHeader";
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
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[{ title: "All requests" }]}
        rightContent={
          <Space>
            {hasPlus && (
              <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_CREATE]}>
                <SubmitPrivacyRequest />
              </Restrict>
            )}
            <ActionButtons />
          </Space>
        }
        data-testid="privacy-requests"
      />

      <RequestTable />
    </>
  );
};

export default PrivacyRequestsContainer;
