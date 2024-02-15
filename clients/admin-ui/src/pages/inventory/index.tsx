import type { NextPage } from "next";
import { Box, Flex, Heading, Text } from "@fidesui/react";
import Layout from "~/features/common/Layout";
import { InventoryTable } from "./InventoryTable";

const Inventory: NextPage = () => {
  return (
    <Layout title="Inventory">
      <>
        <Box mb={4}>
          <Heading
            fontSize="2xl"
            fontWeight="semibold"
            mb={2}
            data-testid="header"
          >
            Inventory
          </Heading>
        </Box>
        <Flex>
          <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "60%" }}>
            Review and manage your properties below. Properties are the
            locations you have configured to manage data governance and detect
            potential data governance risks.
          </Text>
        </Flex>
      </>
      <InventoryTable />
    </Layout>
  );
};

export default Inventory;
