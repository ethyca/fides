import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetPropertyByIdQuery,
  useUpdatePropertyMutation,
} from "~/features/properties/property.slice";
import PropertyForm, {
  PropertyFormValues,
} from "~/features/properties/PropertyForm";
import { FormValues, PropertyForm } from "~/features/properties/PropertyForm";
import { isErrorResult } from "~/types/errors";

const EditPropertyPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const { id: propertyId } = router.query;
  const { data, error, isLoading } = useGetPropertyByIdQuery(
    propertyId as string,
  );
  const [updateProperty] = useUpdatePropertyMutation();

  const handleSubmit = async (values: PropertyFormValues) => {
    // We do not support adding messaging templates through the property form. This ensures we do not overwrite
    // previously-configured messaging templates.
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { id, messaging_templates, ...updateValues } = values;

    const result = await updateProperty({ id: id!, property: updateValues });

    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
      return;
    }

    message.success(`Property ${values.name} updated successfully`);
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the property"
      />
    );
  }

  return (
    <Layout title={data?.name ?? "Property"}>
      <PageHeader
        heading="Properties"
        breadcrumbItems={[
          {
            title: "All properties",
            href: PROPERTIES_ROUTE,
          },
          {
            title: data?.name ?? "Property",
          },
        ]}
      />
      <div className="max-w-[720px]">
        <PropertyForm
          property={data}
          isLoading={isLoading}
          handleSubmit={handleSubmit}
        />
      </div>
    </Layout>
  );
};

export default EditPropertyPage;
