import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useCreatePropertyMutation } from "~/features/properties/property.slice";
import { FormValues, PropertyForm } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

const AddPropertyPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const [createProperty] = useCreatePropertyMutation();

  const handleSubmit = async (values: FormValues) => {
    const result = await createProperty(
      values as Parameters<typeof createProperty>[0],
    );

    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
      return;
    }

    const prop = result.data;
    message.success(`Property ${values.name} created successfully`);
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
      <div className="max-w-[720px]">
        <PropertyForm handleSubmit={handleSubmit} />
      </div>
    </Layout>
  );
};

export default AddPropertyPage;
