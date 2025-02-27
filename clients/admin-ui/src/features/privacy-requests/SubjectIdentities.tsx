import { AntTag as Tag, Divider, Flex, Heading, Text } from "fidesui";

import { PrivacyRequestEntity } from "./types";

type SubjectIdentitiesProps = {
  subjectRequest: PrivacyRequestEntity;
};

const SubjectIdentities = ({ subjectRequest }: SubjectIdentitiesProps) => {
  const { custom_privacy_request_fields: customPrivacyRequestFields } =
    subjectRequest;
  return (
    <div>
      {customPrivacyRequestFields &&
        Object.keys(customPrivacyRequestFields).length > 0 && (
          <>
            <Heading
              color="gray.900"
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
                    color="gray.900"
                    fontWeight="500"
                  >
                    {item.label}:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {Array.isArray(item.value)
                      ? item.value.join(", ")
                      : item.value}
                  </Text>
                  <Tag>Unverified</Tag>
                </Flex>
              ))}
          </>
        )}
    </div>
  );
};

export default SubjectIdentities;
