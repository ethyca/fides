import { Button, Icons, Result } from "fidesui";
import NextLink from "next/link";

import { PRIVACY_ASSESSMENTS_EVALUATE_ROUTE } from "~/features/common/nav/routes";

export const EmptyState = () => (
  <Result
    icon={<Icons.Document size={48} />}
    title="No assessments run yet"
    subTitle="Run assessments to evaluate your systems against regulatory frameworks and identify compliance gaps."
    extra={
      <NextLink href={PRIVACY_ASSESSMENTS_EVALUATE_ROUTE} passHref>
        <Button type="primary" icon={<Icons.Add />}>
          Run assessment
        </Button>
      </NextLink>
    }
    className="mt-20"
  />
);
