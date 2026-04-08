import { Spin, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useAssignConsumerPurposesMutation,
  useGetDataConsumerByIdQuery,
  useUpdateDataConsumerMutation,
} from "~/features/data-consumers/data-consumer.slice";
import DataConsumerForm, {
  DataConsumerFormValues,
} from "~/features/data-consumers/DataConsumerForm";
import { RTKErrorResult } from "~/types/errors/api";

const EditDataConsumerPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const { id: consumerId } = router.query;

  const {
    data: consumer,
    error,
    isLoading,
  } = useGetDataConsumerByIdQuery(consumerId as string, {
    skip: !consumerId,
  });

  const [updateDataConsumer] = useUpdateDataConsumerMutation();
  const [assignConsumerPurposes] = useAssignConsumerPurposesMutation();

  const handleSubmit = async (values: DataConsumerFormValues) => {
    if (!consumerId) {
      return;
    }

    const { purposeFidesKeys, ...consumerPayload } = values;

    try {
      await updateDataConsumer({
        id: consumerId as string,
        ...consumerPayload,
      }).unwrap();

      // Check if purposes changed and assign if so
      const existingPurposes = consumer?.purpose_fides_keys ?? [];
      const purposesChanged =
        JSON.stringify([...purposeFidesKeys].sort()) !==
        JSON.stringify([...existingPurposes].sort());

      if (purposesChanged) {
        try {
          await assignConsumerPurposes({
            id: consumerId as string,
            purposeFidesKeys,
          }).unwrap();
        } catch (assignErr) {
          message.error(
            `Data consumer updated but failed to assign purposes: ${getErrorMessage(assignErr as RTKErrorResult["error"])}`,
          );
          return;
        }
      }

      message.success(`Data consumer "${values.name}" updated successfully`);
    } catch (err) {
      message.error(getErrorMessage(err as RTKErrorResult["error"]));
    }
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the data consumer"
      />
    );
  }

  if (isLoading) {
    return (
      <Layout title="Data consumer">
        <Spin />
      </Layout>
    );
  }

  return (
    <Layout title={consumer?.name ?? "Data consumer"}>
      <PageHeader
        heading="Data consumers"
        breadcrumbItems={[
          {
            title: "All data consumers",
            href: DATA_CONSUMERS_ROUTE,
          },
          {
            title: consumer?.name ?? "Data consumer",
          },
        ]}
      />
      <DataConsumerForm consumer={consumer} handleSubmit={handleSubmit} />
    </Layout>
  );
};

export default EditDataConsumerPage;
