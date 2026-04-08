import { ChakraBox as Box, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { useCreatePropertyMutation } from "~/features/properties/property.slice";
import PropertyForm, { FormValues } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

const AddPropertyPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const [createProperty] = useCreatePropertyMutation();

  const handleSubmit = async (values: FormValues) => {
    const result = await createProperty(values);

    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
      return;
    }

    const prop = result.data;
    message.success(`Property ${values.name} created successfully`);
    router.push(`${PROPERTIES_ROUTE}/${prop.id}`);
  };

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Properties"
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
      </SidePanel>
      <Layout title="Add property">
        <Box maxWidth="720px">
          <PropertyForm handleSubmit={handleSubmit} />
        </Box>
      </Layout>
    </>
  );
};

export default AddPropertyPage;
