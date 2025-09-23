import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import CustomFieldFormV2 from "~/features/custom-fields/v2/CustomFieldFormV2";

const CustomFieldNewPage = () => {
  return (
    <Layout title="New custom field" mainProps={{ maxWidth: "720px" }}>
      <PageHeader
        heading="Custom fields"
        breadcrumbItems={[
          { title: "All custom fields", href: CUSTOM_FIELDS_ROUTE },
          { title: "Create new" },
        ]}
      />
      <CustomFieldFormV2 />
    </Layout>
  );
};

export default CustomFieldNewPage;
