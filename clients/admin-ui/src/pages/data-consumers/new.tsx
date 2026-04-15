import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import DataConsumerForm, {
  DataConsumerFormValues,
} from "~/features/data-consumers/DataConsumerForm";

const NewDataConsumerPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();

  const handleSubmit = (values: DataConsumerFormValues) => {
    // Mock — just show success and navigate back
    message.success(`Data consumer "${values.name}" created successfully`);
    router.push(DATA_CONSUMERS_ROUTE);
  };

  return (
    <FixedLayout title="Add data consumer">
      <PageHeader
        heading="Data consumers"
        breadcrumbItems={[
          { title: "All data consumers", href: DATA_CONSUMERS_ROUTE },
          { title: "Add data consumer" },
        ]}
      />
      <DataConsumerForm onSubmit={handleSubmit} />
    </FixedLayout>
  );
};

export default NewDataConsumerPage;
