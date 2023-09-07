import { Divider, Flex, Heading, Tag, Text } from "@fidesui/react";
import { useState } from "react";

import PII from "../common/PII";
import PIIToggle from "../common/PIIToggle";
import { PrivacyRequestEntity } from "./types";
import { snakeToSentenceCase } from "../common/utils";

type SubjectIdentitiesProps = {
  subjectRequest: PrivacyRequestEntity;
};

const SubjectIdentities = ({ subjectRequest }: SubjectIdentitiesProps) => {
  const {
    identity,
    identity_verified_at,
    custom_metadata_approved_at,
    custom_metadata,
  } = subjectRequest;
  const [revealPII, setRevealPII] = useState(false);

  return (
    <>
      <Flex direction="row" justifyContent="space-between">
        <Heading color="gray.900" fontSize="lg" fontWeight="semibold" mb={4}>
          Subject identities
        </Heading>
        <Flex flexShrink={0} alignItems="flex-start">
          <PIIToggle revealPII={revealPII} onChange={setRevealPII} />
          <Text
            fontSize="xs"
            ml={2}
            size="sm"
            color="gray.600"
            fontWeight="500"
          >
            Reveal PII
          </Text>
        </Flex>
      </Flex>
      <Divider />

      {identity.email && (
        <Flex alignItems="center">
          <Text
            mt={4}
            mb={4}
            mr={2}
            fontSize="sm"
            color="gray.900"
            fontWeight="500"
          >
            Email:
          </Text>
          <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
            <PII
              data={identity.email ? identity.email : ""}
              revealPII={revealPII}
            />
          </Text>
          <Tag color="white" bg="primary.400" fontWeight="medium" fontSize="sm">
            {identity_verified_at ? "Verified" : "Unverified"}
          </Tag>
        </Flex>
      )}
      {identity.phone_number && (
        <Flex alignItems="flex-start">
          <Text mb={4} mr={2} fontSize="sm" color="gray.900" fontWeight="500">
            Mobile:
          </Text>
          <Text color="gray.600" fontWeight="500" fontSize="sm">
            <PII
              data={identity.phone_number ? identity.phone_number : ""}
              revealPII={revealPII}
            />
          </Text>
          <Tag color="white" bg="primary.400" fontWeight="medium" fontSize="sm">
            {identity_verified_at ? "Verified" : "Unverified"}
          </Tag>
        </Flex>
      )}
      {custom_metadata && (
        <>
          <Heading color="gray.900" fontSize="sm" fontWeight="semibold" mb={4}>
            Additional inputs
          </Heading>
          {Object.entries(custom_metadata)
            .filter(([key, item]) => item["value"])
            .map(([key, item]) => (
              <Flex alignItems="flex-start" key={key}>
                <Text
                  mb={4}
                  mr={2}
                  fontSize="sm"
                  color="gray.900"
                  fontWeight="500"
                >
                  {snakeToSentenceCase(key)}:
                </Text>
                <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                  <PII data={item["value"]} revealPII={revealPII} />
                </Text>
                <Tag
                  color="white"
                  bg="primary.400"
                  fontWeight="medium"
                  fontSize="sm"
                >
                  Unverified
                </Tag>
              </Flex>
            ))}
        </>
      )}
    </>
  );
};

export default SubjectIdentities;
