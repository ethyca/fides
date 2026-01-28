"use client";

import { useMessage } from "fidesui";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { useConfig } from "~/features/common/config.slice";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { PrivacyRequestOption } from "~/types/config";

import PrivacyRequestForm from "../modals/privacy-request-modal/PrivacyRequestForm";

type PrivacyRequestFormPageProps = {
  actionKey: string;
};

const PrivacyRequestFormPage = ({ actionKey }: PrivacyRequestFormPageProps) => {
  const config = useConfig();
  const router = useRouter();
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

  const messageApi = useMessage();

  const policyKey = decodeURIComponent(actionKey);

  const action = config.actions.find((a) => a.policy_key === policyKey) as
    | PrivacyRequestOption
    | undefined;

  // Update verification requirement from API
  useEffect(() => {
    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required,
      );
    }
  }, [getIdVerificationConfigQuery]);

  useEffect(() => {
    if (!action) {
      messageApi.error(`Invalid action key "${policyKey}" for privacy request`);
      router.push("/");
    }
  }, [action, policyKey, messageApi, router]);

  const handleExit = () => {
    router.push("/");
  };

  const handleSetCurrentView = (view: string) => {
    // Navigate to verification page
    if (view === "identityVerification") {
      router.push(`/privacy-request/${encodeURIComponent(policyKey)}/verify`);
    }
  };

  const handleSetPrivacyRequestId = (id: string) => {
    // Store the request ID in sessionStorage for the verification page
    if (typeof window !== "undefined") {
      sessionStorage.setItem("privacyRequestId", id);
    }
  };

  const handleSuccessWithoutVerification = () => {
    // Navigate to success page when verification is not required
    router.push(`/privacy-request/${encodeURIComponent(policyKey)}/success`);
  };

  return (
    <PrivacyRequestForm
      onExit={handleExit}
      openAction={action}
      setCurrentView={handleSetCurrentView}
      setPrivacyRequestId={handleSetPrivacyRequestId}
      isVerificationRequired={isVerificationRequired}
      onSuccessWithoutVerification={handleSuccessWithoutVerification}
    />
  );
};

export default PrivacyRequestFormPage;
