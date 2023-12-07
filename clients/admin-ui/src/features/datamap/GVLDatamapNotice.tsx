import { Box } from "@fidesui/react";

import EmptyTableState from "~/features/common/table/EmptyTableState";

const GVLDatamapNotice = () => (
  <Box mb="6" maxW="720px" data-testid="GVL-datamap-notice">
    <EmptyTableState
      title="GVL and AC vendors are not displayed"
      description="Global Vendor List and Google Additional Consent vendors are not displayed on the data map for performance reasons. An enhancement is in the works!"
    />
  </Box>
);

export default GVLDatamapNotice;
