import { Box, Link, Text } from "@fidesui/react";
import EmptyTableState from "~/features/common/table/EmptyTableState";

const GVLNotice = () => {
  return (
    <Box mb="6" maxW="720px">
      <EmptyTableState
        title="This system is part of the TCF Global Vendor Listing"
        description={
          <Text>
            Some form elements below will be disabled as they cannot be edited
            if they are populated directly from the Global Vendor List.{" "}
            <Link
              href="https://fid.es/tcf_gvl"
              isExternal
              color="complimentary.500"
            >
              For more information on the Global Vendor List, click here.
            </Link>
          </Text>
        }
      />
    </Box>
  );
};

export default GVLNotice;
