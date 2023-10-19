import { Button } from "@fidesui/react";
import { useRouter } from "next/router";

import { ADD_MULTIPLE_VENDORS_ROUTE } from "~/features/common/nav/v2/routes";

export const AddMultipleVendors = () => {
  const router = useRouter();
  return (
    <Button
      onClick={() => {
        router.push(ADD_MULTIPLE_VENDORS_ROUTE);
      }}
      data-testid="add-multiple-vendors-btn"
      size="sm"
      colorScheme="primary"
    >
      Add multiple vendors
    </Button>
  );
};
