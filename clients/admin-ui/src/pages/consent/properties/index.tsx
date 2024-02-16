import { Box, Flex, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";

import { PropertiesTable } from "./components/PropertiesTable";

const Properties: NextPage = () => (
    <Layout title="Properties">
      <>
        <Box mb={4}>
          <Heading
            fontSize="2xl"
            fontWeight="semibold"
            mb={2}
            data-testid="header"
          >
            Properties
          </Heading>
        </Box>
        <Flex>
          <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "60%" }}>
            Review and manage your properties below. Properties are the
            locations you have configured for consent management such as a
            website or mobile app.
          </Text>
        </Flex>
      </>
      <PropertiesTable />
    </Layout>
  );

export default Properties;
