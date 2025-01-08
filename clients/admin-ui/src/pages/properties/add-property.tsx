import { Box, useToast } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useCreatePropertyMutation } from "~/features/properties/property.slice";
import PropertyForm, { FormValues } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

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
      <PageHeader
        heading="Properties"
        breadcrumbItems={[
          {
            title: "All properties",
            href: PROPERTIES_ROUTE,
          },
          {
            title: "Add property",
          },
        ]}
      />
      <Box maxWidth="720px">
        <PropertyForm handleSubmit={handleSubmit} />
      </Box>
    </Layout>
  );
};

export default AddPropertyPage;
