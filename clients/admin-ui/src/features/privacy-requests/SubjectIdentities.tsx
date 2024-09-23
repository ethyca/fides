import { Divider, Flex, Heading, Tag, Text } from "fidesui";

import { PrivacyRequestEntity } from "./types";

type SubjectIdentitiesProps = {
  subjectRequest: PrivacyRequestEntity;
};

const SubjectIdentities = ({ subjectRequest }: SubjectIdentitiesProps) => {
  const {
    identity,
    identity_verified_at: identityVerifiedAt,
    custom_privacy_request_fields: customPrivacyRequestFields,
  } = subjectRequest;
  return (
    <>
      <Flex direction="row" justifyContent="space-between">
        <Heading
          color="neutral.900"
          fontSize="lg"
          fontWeight="semibold"
          mb={4}
          mt={4}
        >
          Subject identities
        </Heading>
      </Flex>
      <Divider mb={4} />
      {Object.entries(identity)
        .filter(([, { value }]) => value !== null)
        .map(([key, { value, label }]) => (
          <Flex key={key} alignItems="flex-start">
            <Text
              mb={4}
              mr={2}
              fontSize="sm"
              color="neutral.900"
              fontWeight="500"
            >
              {label}:
            </Text>
            <Text color="neutral.600" fontWeight="500" fontSize="sm" mr={2}>
              {value || ""}
            </Text>
            <Tag
              color="white"
              bg="primary.400"
              fontWeight="medium"
              fontSize="sm"
            >
              {identityVerifiedAt ? "Verified" : "Unverified"}
            </Tag>
          </Flex>
        ))}
      {customPrivacyRequestFields &&
        Object.keys(customPrivacyRequestFields).length > 0 && (
          <>
            <Heading
              color="neutral.900"
              fontSize="lg"
              fontWeight="semibold"
              mt={4}
              mb={4}
            >
              Custom request fields
            </Heading>
            <Divider mb={4} />
            {Object.entries(customPrivacyRequestFields)
              .filter(([, item]) => item.value)
              .map(([key, item]) => (
                <Flex alignItems="flex-start" key={key}>
                  <Text
                    mb={4}
                    mr={2}
                    fontSize="sm"
                    color="neutral.900"
                    fontWeight="500"
                  >
                    {item.label}:
                  </Text>
                  <Text
                    color="neutral.600"
                    fontWeight="500"
                    fontSize="sm"
                    mr={2}
                  >
                    {Array.isArray(item.value)
                      ? item.value.join(", ")
                      : item.value}
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
