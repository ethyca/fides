"use client";

import { Button, Flex, Text, useMessage } from "fidesui";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";

import { decodePolicyKey } from "~/common/policy-key";
import { useConfig } from "~/features/common/config.slice";
import { useProperty } from "~/features/common/property.slice";
import { useGetIdVerificationConfigQuery } from "~/features/id-verification";
import { IDPLoginButtons } from "~/features/idp-verification";
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
  const property = useProperty();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const [isVerificationRequired, setIsVerificationRequired] =
    useState<boolean>(false);

  const isIDPVerification =
    config.identity_verification?.method === "idp";
  const idpProviders = config.identity_verification?.idp_providers ?? [];

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

  // Update verification requirement from API (OTP path only)
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

  // Show error toast when redirected back from failed IDP callback
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

  const handleValidateForIDP = useCallback(async (): Promise<boolean> => {
    // TODO: validate custom fields before IDP redirect
    return true;
  }, []);

  if (isIDPVerification && idpProviders.length > 0 && selectedAction) {
    return (
      <Flex vertical gap="middle">
        <Text type="secondary">{selectedAction.description}</Text>
        {selectedAction.description_subtext?.map((paragraph) => (
          <Text key={paragraph} size="sm">
            {paragraph}
          </Text>
        ))}
        <IDPLoginButtons
          providers={idpProviders}
          actionKey={actionKey}
          basePath={basePath || "/"}
          formData={{
            policy_key: selectedAction.policy_key ?? policyKey,
            property_id: property?.id ?? undefined,
          }}
          onValidate={handleValidateForIDP}
        />
        <Button type="default" variant="outlined" onClick={handleExit} block>
          {selectedAction.cancelButtonText || "Cancel"}
        </Button>
      </Flex>
    );
  }

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
