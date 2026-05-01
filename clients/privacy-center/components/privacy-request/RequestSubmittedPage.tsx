"use client";

import { Button, Flex, Image, Text, Title } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React from "react";

import useActionFromRoute from "~/common/hooks/useActionFromRoute";

const RequestSubmittedPage = () => {
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";
  const actionKey = params?.actionKey as string | undefined;
  const action = useActionFromRoute(actionKey);

  const handleContinue = () => {
    router.push(basePath || "/");
  };

  return (
    <Flex gap="medium" vertical align="center">
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
