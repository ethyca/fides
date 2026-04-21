"use client";

import { useMessage } from "fidesui";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import React, { useEffect, useState } from "react";

import { decodePolicyKey } from "~/common/policy-key";
import { useConfig } from "~/features/common/config.slice";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { IDP_SESSION_KEYS } from "~/features/idp-verification/constants";
import { PrivacyRequestOption } from "~/types/config";

import PrivacyRequestForm from "../modals/privacy-request-modal/PrivacyRequestForm";

type PrivacyRequestFormPageProps = {
  actionKey: string;
};

const PrivacyRequestFormPage = ({ actionKey }: PrivacyRequestFormPageProps) => {
  const config = useConfig();
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);

  const isIDPVerification = config.identity_verification?.method === "idp";

  const [idpVerificationToken, setIdpVerificationToken] = useState<
    string | null
  >(null);

  useEffect(() => {
    if (isIDPVerification && typeof window !== "undefined") {
      const token = sessionStorage.getItem(
        IDP_SESSION_KEYS.VERIFICATION_TOKEN,
      );
      setIdpVerificationToken(token);
    }
  }, [isIDPVerification]);

  const getIdVerificationConfigQuery = useGetIdVerificationConfigQuery(
    undefined,
    { skip: isIDPVerification },
  );

  const messageApi = useMessage();

  const decoded = decodePolicyKey(actionKey);
  const colonIndex = decoded.indexOf(":");
  const actionIndex =
    colonIndex !== -1 ? parseInt(decoded.slice(0, colonIndex), 10) : NaN;
  const policyKey = colonIndex !== -1 ? decoded.slice(colonIndex + 1) : decoded;

  const actions = config.actions ?? [];
  const selectedAction = (
    !Number.isNaN(actionIndex) && actions[actionIndex]?.policy_key === policyKey
      ? actions[actionIndex]
      : actions.find((action) => action.policy_key === policyKey)
  ) as PrivacyRequestOption | undefined;

  useEffect(() => {
    if (getIdVerificationConfigQuery.isSuccess) {
      setIsVerificationRequired(
        getIdVerificationConfigQuery.data.identity_verification_required,
      );
    }
  }, [getIdVerificationConfigQuery]);

  useEffect(() => {
    if (!selectedAction) {
      messageApi.error(`Invalid action key "${policyKey}" for privacy request`);
      router.push(basePath || "/");
    }
  }, [selectedAction, policyKey, messageApi, router, basePath]);

  useEffect(() => {
    if (searchParams?.get("error") === "idp_failed") {
      messageApi.error("Identity verification failed. Please try again.");
    }
  }, [searchParams, messageApi]);

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
      idpVerificationToken={idpVerificationToken}
    />
  );
};

export default PrivacyRequestFormPage;
