import { Box, Heading, Text, useToast } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useCreatePropertyMutation } from "~/features/properties/property.slice";
import PropertyForm, { FormValues } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

const Header = () => (
  <Box display="flex" alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Add property
    </Heading>
  </Box>
);

const AddPropertyPage: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const [createProperty] = useCreatePropertyMutation();

  const handleSubmit = async (values: FormValues) => {
    const result = await createProperty(values);

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    const prop = result.data;
    toast(successToastParams(`Property ${values.name} created successfully`));
    router.push(`${PROPERTIES_ROUTE}/${prop.id}`);
  };

  return (
    <Layout title="Add property">
      <Header />
      <Box maxWidth="720px" pt={2}>
        <Text fontSize="sm">Add new property to Fides here.</Text>
        <PropertyForm handleSubmit={handleSubmit} />
      </Box>
    </Layout>
  );
};

export default AddPropertyPage;
