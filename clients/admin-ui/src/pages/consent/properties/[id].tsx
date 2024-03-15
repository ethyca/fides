import { Box, Heading, Text, useToast } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useGetPropertyByIdQuery,
  useUpdatePropertyMutation,
} from "~/features/properties/property.slice";
import PropertyForm, { FormValues } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

const EditPropertyPage: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const { id: propertyId } = router.query;
  const { data } = useGetPropertyByIdQuery(propertyId as string);
  const [updateProperty] = useUpdatePropertyMutation();

  const handleSubmit = async (values: FormValues) => {
    const { id, ...updateValues } = values;

    const result = await updateProperty({ id: id!, property: updateValues });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    toast(successToastParams(`Property ${values.name} updated successfully`));
    router.push(`${PROPERTIES_ROUTE}`);
  };

  if (!data) {
    return null;
  }

  return (
    <Layout title={data.name}>
      <Box display="flex" alignItems="center" data-testid="header">
        <Heading fontSize="2xl" fontWeight="semibold">
          Edit {data.name}
        </Heading>
      </Box>
      <Box maxWidth="720px" pt={2}>
        <Text fontSize="sm">Edit your existing property here.</Text>
        <PropertyForm property={data} handleSubmit={handleSubmit} />
      </Box>
    </Layout>
  );
};

export default EditPropertyPage;
