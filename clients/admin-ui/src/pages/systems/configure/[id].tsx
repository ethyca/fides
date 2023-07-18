import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Spinner,
  Text,
  toast,
  useToast,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import EditSystemFlow from "~/features/system/EditSystemFlow";

const ConfigureSystem: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [initialTabIndex, setInitialTabIndex] = useState(0);
  let systemId = "";
  if (router.query.id) {
    systemId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  useEffect(() => {
    dispatch(setActiveSystem(system));
  }, [system, dispatch]);

  useEffect(() => {
    const status = router.query.status;

    if (status) {
      if (status === "succeeded") {
        toast(successToastParams(`Integration successfully authorized.`));
      } else {
        toast(errorToastParams(`Failed to authorize integration.`));
      }
      // create a new url without the status query param
      let newQuery = { ...router.query };
      delete newQuery.status;
      const newUrl = {
        pathname: router.pathname,
        query: newQuery,
      };

      // replace the current history entry
      router.replace(newUrl, undefined, { shallow: true });

      setInitialTabIndex(3);
    }
  }, [router.query]);

  if (isLoading) {
    return (
      <Layout title="Systems">
        <Spinner />
      </Layout>
    );
  }

  return (
    <Layout title="Systems">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Configure your system
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href={SYSTEM_ROUTE}>System Integrations</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Configure your integration</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      {!system ? (
        <Text data-testid="system-not-found">
          Could not find a system with id {systemId}
        </Text>
      ) : (
        <EditSystemFlow initialTabIndex={initialTabIndex} />
      )}
    </Layout>
  );
};

export default ConfigureSystem;
