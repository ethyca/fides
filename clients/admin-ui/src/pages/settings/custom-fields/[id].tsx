import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import CustomFieldForm from "~/features/custom-fields/CustomFieldForm";
import { useGetCustomFieldDefinitionByIdQuery } from "~/features/plus/plus.slice";

const CustomFieldDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;

  const {
    data: customField,
    isLoading,
    error,
  } = useGetCustomFieldDefinitionByIdQuery({
    id: id as string,
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the custom field ${id}`}
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Custom fields"
          breadcrumbItems={[
            { title: "All custom fields", href: CUSTOM_FIELDS_ROUTE },
            { title: customField?.name ?? (id as string) },
          ]}
        />
      </SidePanel>
      <Layout title="Edit custom field" mainProps={{ maxWidth: "720px" }}>
        <CustomFieldForm initialField={customField} isLoading={isLoading} />
      </Layout>
    </>
  );
};

export default CustomFieldDetailPage;
