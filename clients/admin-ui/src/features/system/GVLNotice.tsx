import { Box, Link } from "fidesui";

import EmptyTableState from "~/features/common/table/EmptyTableState";

const GVLNotice = () => (
  <Box mb="6" maxW="720px" data-testid="locked-for-GVL-notice">
    <EmptyTableState
      title="This system is part of the TCF Global Vendor List (GVL)"
      description={
        <>
          As a result, certain fields are not editable as they come directly
          from Fides Compass and the Global Vendor List (GVL). In some cases,
          where the legal basis has been declared to be flexible, you may update
          the legal basis for particular data uses.{" "}
          <Link
            href="https://fid.es/tcf_gvl"
            isExternal
            color="complimentary.500"
          >
            For more information on the Global Vendor List, click here.
          </Link>
        </>
      }
    />
  </Box>
);

export default GVLNotice;
