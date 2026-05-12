"use client";

import { useMessage } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import useActionFromRoute from "~/common/hooks/useActionFromRoute";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";

import PrivacyRequestForm from "../modals/privacy-request-modal/PrivacyRequestForm";

type PrivacyRequestFormPageProps = {
  actionKey: string;
};

const PrivacyRequestFormPage = ({ actionKey }: PrivacyRequestFormPageProps) => {
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();
  const messageApi = useMessage();
  const selectedAction = useActionFromRoute(actionKey);

  // Update verification requirement from API
  useEffect(() => {
    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required,
      );
    }
  }, [getIdVerificationConfigQuery]);

  useEffect(() => {
    if (!selectedAction) {
      messageApi.error(`Invalid action key "${actionKey}" for privacy request`);
      router.push(basePath || "/");
    }
  }, [selectedAction, actionKey, messageApi, router, basePath]);

  const handleExit = () => {
    router.push(basePath || "/");
  };

  const handleSetCurrentView = (view: string) => {
    if (view === "identityVerification") {
      router.push(`${basePath}/privacy-request/${actionKey}/verify`);
    }
  };

  const handleSetPrivacyRequestId = (id: string) => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("privacyRequestId", id);
    }
  };

  const handleSuccessWithoutVerification = () => {
    router.push(`${basePath}/privacy-request/${actionKey}/success`);
  };

  return (
    <PrivacyRequestForm
      onExit={handleExit}
      openAction={selectedAction}
      setCurrentView={handleSetCurrentView}
      setPrivacyRequestId={handleSetPrivacyRequestId}
      isVerificationRequired={isVerificationRequired}
      onSuccessWithoutVerification={handleSuccessWithoutVerification}
    />
  );
};

export default PrivacyRequestFormPage;
