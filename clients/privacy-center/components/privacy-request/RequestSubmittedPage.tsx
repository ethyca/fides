"use client";

import { Button, Flex, Image, Text, Title } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React from "react";

import { decodePolicyKey } from "~/common/policy-key";
import { useConfig } from "~/features/common/config.slice";
import { PrivacyRequestOption } from "~/types/config";

const RequestSubmittedPage = () => {
  const config = useConfig();
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const actionKey = params?.actionKey as string | undefined;

  let action: PrivacyRequestOption | undefined;
  if (actionKey) {
    const decoded = decodePolicyKey(actionKey);
    const colonIndex = decoded.indexOf(":");
    const actionIndex =
      colonIndex !== -1 ? parseInt(decoded.slice(0, colonIndex), 10) : NaN;
    const policyKey =
      colonIndex !== -1 ? decoded.slice(colonIndex + 1) : decoded;
    const actions = config.actions ?? [];
    action = (
      !Number.isNaN(actionIndex) &&
      actions[actionIndex]?.policy_key === policyKey
        ? actions[actionIndex]
        : actions.find((a) => a.policy_key === policyKey)
    ) as PrivacyRequestOption | undefined;
  }

  const handleContinue = () => {
    router.push(basePath || "/");
  };

  return (
    <Flex gap="middle" vertical align="center">
      <Image
        src="/green-check.svg"
        alt="green-checkmark"
        width="48px"
        height="48px"
        preview={false}
      />
      {action?.success_title && (
        <Title level={3} style={{ textAlign: "center", margin: 0 }}>
          {action.success_title}
        </Title>
      )}
      <Text style={{ textAlign: "center" }}>
        {action?.success_description ??
          "Thanks for your request. A member of our team will review and be in contact with you shortly."}
      </Text>
      <Button
        type="primary"
        onClick={handleContinue}
        block
        style={{ marginTop: "24px" }}
      >
        {action?.success_button_text ?? "Return home"}
      </Button>
    </Flex>
  );
};

export default RequestSubmittedPage;
