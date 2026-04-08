import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import CustomFieldForm from "~/features/custom-fields/CustomFieldForm";

const CustomFieldNewPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Custom fields"
          breadcrumbItems={[
            { title: "All custom fields", href: CUSTOM_FIELDS_ROUTE },
            { title: "Create new" },
          ]}
        />
      </SidePanel>
      <Layout title="New custom field" mainProps={{ maxWidth: "720px" }}>
        <CustomFieldForm />
      </Layout>
    </>
  );
};

export default CustomFieldNewPage;
