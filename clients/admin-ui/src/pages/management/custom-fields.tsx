import { Box, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
} from "~/features/plus/plus.slice";

const CustomFields: NextPage = () => {
  useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);

  return (
    <Layout title="Custom fields">
      <Box data-testid="custom-fields-management">
        <Heading marginBottom={4} fontSize="2xl">
          Manage custom fields
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={10} fontSize="sm">
            Custom fields provide organizations with the capability to capture
            metrics that are unique to their specific needs, allowing them to
            create customized reports. These fields can be added to either
            systems or elements within a taxonomy, and once added, they become
            reportable fields that are visible on the data map.
          </Text>
          <Box background="gray.50" padding={2}>
            {customFields.map((customField) => (
              <Box key={customField.id}>{customField.name}</Box>
            ))}
          </Box>
        </Box>
      </Box>
    </Layout>
  );
};
export default CustomFields;
