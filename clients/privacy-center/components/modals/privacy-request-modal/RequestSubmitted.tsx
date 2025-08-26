import { AntFlex as Flex, AntImage as Image, AntText as Text } from "fidesui";
import React from "react";

const RequestSubmitted = () => (
  <>
    <Flex>
      <Image
        src="/green-check.svg"
        alt="green-checkmark"
        width="48px"
        height="48px"
      />
    </Flex>
    <Text size="sm">
      Thanks for your request. A member of our team will review and be in
      contact with you shortly.
    </Text>
  </>
);

export default RequestSubmitted;
