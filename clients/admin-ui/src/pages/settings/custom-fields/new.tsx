import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import CustomFieldForm from "~/features/custom-fields/CustomFieldForm";

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
      <CustomFieldForm />
    </Layout>
  );
};

export default CustomFieldNewPage;
