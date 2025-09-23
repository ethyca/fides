import { AntSkeleton as Skeleton } from "fidesui";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import CustomFieldFormV2 from "~/features/custom-fields/v2/CustomFieldFormV2";
import { useGetCustomFieldDefinitionByIdQuery } from "~/features/plus/plus.slice";

const SkeletonCustomFieldForm = () => {
  return (
    <Skeleton active>
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Button />
    </Skeleton>
  );
};

const CustomFieldDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;

  const { data: customField, isLoading } = useGetCustomFieldDefinitionByIdQuery(
    { id: id as string },
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
      {isLoading ? (
        <SkeletonCustomFieldForm />
      ) : (
        <CustomFieldFormV2 initialField={customField} />
      )}
    </Layout>
  );
};

export default CustomFieldDetailPage;
