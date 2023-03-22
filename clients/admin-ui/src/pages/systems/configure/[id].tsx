import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import { SYSTEM_ROUTE } from "~/constants";
import Layout from "~/features/common/Layout";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import EditSystemFlow from "~/features/system/EditSystemFlow";

const ConfigureSystem: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
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
            <NextLink href={SYSTEM_ROUTE}>System Connections</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Configure your connection</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      {!system ? (
        <Text>Could not find a system with id {systemId}</Text>
      ) : (
        <EditSystemFlow />
      )}
    </Layout>
  );
};

export default ConfigureSystem;
