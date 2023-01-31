import { Divider, Flex, Heading, Text } from "@fidesui/react";
import { useState } from "react";

import PII from "../common/PII";
import PIIToggle from "../common/PIIToggle";
import { PrivacyRequestEntity } from "./types";

type SubjectIdentitiesProps = {
  subjectRequest: PrivacyRequestEntity;
};

const SubjectIdentities = ({ subjectRequest }: SubjectIdentitiesProps) => {
  const { identity } = subjectRequest;
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
        <Text color="gray.600" fontWeight="500" fontSize="sm">
          <PII
            data={identity.email ? identity.email : ""}
            revealPII={revealPII}
          />
        </Text>
      </Flex>
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
      </Flex>
    </>
  );
};

export default SubjectIdentities;
