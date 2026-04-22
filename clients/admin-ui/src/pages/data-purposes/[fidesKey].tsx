import { Button, Flex, Result, Spin } from "fidesui";
import { NextPage } from "next";
import Link from "next/link";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDataPurposeByKeyQuery } from "~/features/data-purposes/data-purpose.slice";
import PurposeDetail from "~/features/data-purposes/PurposeDetail";

const PurposeDetailPage: NextPage = () => {
  const router = useRouter();
  const rawKey = router.query.fidesKey;
  const fidesKey = typeof rawKey === "string" ? rawKey : undefined;

  const {
    data: purpose,
    isLoading,
    isError,
    error,
  } = useGetDataPurposeByKeyQuery(fidesKey ?? "", { skip: !fidesKey });

  const is404 =
    isError &&
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    (error as { status?: number }).status === 404;

  let body: React.ReactNode;
  if (!fidesKey || isLoading) {
    body = (
      <Flex justify="center" className="mt-12">
        <Spin size="large" />
      </Flex>
    );
  } else if (is404 || (!purpose && !isError)) {
    body = (
      <Result
        status="404"
        title="Purpose not found"
        subTitle="This purpose doesn't exist or has been deleted."
        extra={
          <Link href={DATA_PURPOSES_ROUTE}>
            <Button type="primary">Back to purposes</Button>
          </Link>
        }
      />
    );
  } else if (isError) {
    body = (
      <Result
        status="error"
        title="Couldn't load purpose"
        subTitle="Something went wrong. Refresh to try again."
      />
    );
  } else if (purpose) {
    body = <PurposeDetail purpose={purpose} />;
  }

  return (
    <FixedLayout title="Purposes" fullHeight>
      <PageHeader
        heading="Purposes"
        breadcrumbItems={[
          { title: "All purposes", href: DATA_PURPOSES_ROUTE },
          { title: purpose?.name ?? fidesKey ?? "Purpose" },
        ]}
      />
      {body}
    </FixedLayout>
  );
};

export default PurposeDetailPage;
