import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import CustomFieldFormV2 from "~/features/custom-fields/CustomFieldForm";
import { useGetCustomFieldDefinitionByIdQuery } from "~/features/plus/plus.slice";

const CustomFieldDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;

  const { data: customField, isLoading } = useGetCustomFieldDefinitionByIdQuery(
    {
      id: id as string,
    },
  );

  return (
    <Layout title="Edit custom field" mainProps={{ maxWidth: "720px" }}>
      <PageHeader
        heading="Custom fields"
        breadcrumbItems={[
          { title: "All custom fields", href: CUSTOM_FIELDS_ROUTE },
          { title: customField?.name ?? id },
        ]}
      />
      <CustomFieldFormV2 initialField={customField} isLoading={isLoading} />
    </Layout>
  );
};

export default CustomFieldDetailPage;
