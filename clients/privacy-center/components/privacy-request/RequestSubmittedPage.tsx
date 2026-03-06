"use client";

import { Button, Flex, Image, Text } from "fidesui";
import { useParams, useRouter } from "next/navigation";
import React from "react";

const RequestSubmittedPage = () => {
  const router = useRouter();
  const params = useParams();
  const propertyPath = params?.propertyPath as string | undefined;
  const basePath = propertyPath ? `/${propertyPath}` : "";

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
      <Text style={{ textAlign: "center" }}>
        Thanks for your request. A member of our team will review and be in
        contact with you shortly.
      </Text>
      <Button
        type="primary"
        onClick={handleContinue}
        block
        style={{ marginTop: "24px" }}
      >
        Return home
      </Button>
    </Flex>
  );
};

export default RequestSubmittedPage;
