import { Box, Button, Heading, Text, useDisclosure } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import CustomAssetUploadModal from "~/features/custom-assets/CustomAssetUploadModal";

const CustomAssets: NextPage = () => {
  const uploadCustomAssetModal = useDisclosure();

  return (
    <Layout title="Custom Assets">
      <Box data-testid="custom-assets">
        <Heading marginBottom={2} fontSize="2xl">
          Custom Assets
        </Heading>
        <Box maxWidth="720px">
          <Text fontSize="sm">
            View and replace CSS files for the Privacy Experience.
          </Text>
          <Box paddingTop={4}>
            <b>fides.css</b>
            <Button variant="primary" size="sm" ml={2}>
              Download
            </Button>
            <Button
              variant="primary"
              size="sm"
              ml={2}
              onClick={uploadCustomAssetModal.onOpen}
            >
              Upload file
            </Button>
          </Box>
          <CustomAssetUploadModal
            isOpen={uploadCustomAssetModal.isOpen}
            onClose={uploadCustomAssetModal.onClose}
            assetKey="fides_css"
          />
        </Box>
      </Box>
    </Layout>
  );
};

export default CustomAssets;
