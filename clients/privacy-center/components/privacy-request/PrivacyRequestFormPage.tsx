"use client";

import { useMessage } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import { decodePolicyKey } from "~/common/policy-key";
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
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);
  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery();

  const messageApi = useMessage();

  const decoded = decodePolicyKey(actionKey);
  const colonIndex = decoded.indexOf(":");
  const actionIndex =
    colonIndex !== -1 ? parseInt(decoded.slice(0, colonIndex), 10) : NaN;
  const policyKey = colonIndex !== -1 ? decoded.slice(colonIndex + 1) : decoded;

  const action = (
    !Number.isNaN(actionIndex) &&
    config.actions[actionIndex]?.policy_key === policyKey
      ? config.actions[actionIndex]
      : config.actions.find((a) => a.policy_key === policyKey)
  ) as PrivacyRequestOption | undefined;

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
      router.push(basePath || "/");
    }
  }, [action, policyKey, messageApi, router, basePath]);

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
      openAction={action}
      setCurrentView={handleSetCurrentView}
      setPrivacyRequestId={handleSetPrivacyRequestId}
      isVerificationRequired={isVerificationRequired}
      onSuccessWithoutVerification={handleSuccessWithoutVerification}
    />
  );
};

export default PrivacyRequestFormPage;
