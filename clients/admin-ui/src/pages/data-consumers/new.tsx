import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useAssignConsumerPurposesMutation,
  useCreateDataConsumerMutation,
} from "~/features/data-consumers/data-consumer.slice";
import DataConsumerForm, {
  DataConsumerFormValues,
} from "~/features/data-consumers/DataConsumerForm";
import { RTKErrorResult } from "~/types/errors/api";

const NewDataConsumerPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const [createDataConsumer] = useCreateDataConsumerMutation();
  const [assignConsumerPurposes] = useAssignConsumerPurposesMutation();

  const handleSubmit = async (values: DataConsumerFormValues) => {
    const { purposeFidesKeys, ...consumerPayload } = values;

    try {
      const created = await createDataConsumer(consumerPayload).unwrap();

      if (purposeFidesKeys.length > 0) {
        try {
          await assignConsumerPurposes({
            id: created.id,
            purposeFidesKeys,
          }).unwrap();
        } catch (assignErr) {
          message.error(
            `Data consumer created but failed to assign purposes: ${getErrorMessage(assignErr as RTKErrorResult["error"])}`,
          );
          router.push(`${DATA_CONSUMERS_ROUTE}/${created.id}`);
          return;
        }
      }

      message.success(`Data consumer "${values.name}" created successfully`);
      router.push(`${DATA_CONSUMERS_ROUTE}/${created.id}`);
    } catch (err) {
      message.error(getErrorMessage(err as RTKErrorResult["error"]));
    }
  };

  return (
    <Layout title="Add data consumer">
      <PageHeader
        heading="Data consumers"
        breadcrumbItems={[
          {
            title: "All data consumers",
            href: DATA_CONSUMERS_ROUTE,
          },
          {
            title: "Add data consumer",
          },
        ]}
      />
      <DataConsumerForm handleSubmit={handleSubmit} />
    </Layout>
  );
};

export default NewDataConsumerPage;
