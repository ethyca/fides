import { AntButton as Button, AntEmpty as Empty } from "fidesui";
import NextLink from "next/link";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

export const EmptyMonitorsResult = () => (
  <Empty
    image={Empty.PRESENTED_IMAGE_SIMPLE}
    description="All caught up! Set up an integration monitor to track your infrastructure in greater detail."
  >
    <NextLink href={INTEGRATION_MANAGEMENT_ROUTE} passHref legacyBehavior>
      <Button type="primary">Visit integrations</Button>
    </NextLink>
  </Empty>
);
