import { Box, Link } from "@fidesui/react";

import EmptyTableState from "~/features/common/table/EmptyTableState";

const GVLDatamapNotice = () => (
  <Box mb="6" maxW="720px" data-testid="locked-for-GVL-notice">
    <EmptyTableState
      title="GVL vendors are not displayed on the data map"
      description="GVL vendors are not displayed on the data map for performance reasons. An enhancement is in the works!"
    />
  </Box>
);

export default GVLDatamapNotice;
