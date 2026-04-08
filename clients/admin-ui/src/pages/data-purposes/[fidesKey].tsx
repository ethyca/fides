import { Spin, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import {
  useGetDataPurposeByKeyQuery,
  useUpdateDataPurposeMutation,
} from "~/features/data-purposes/data-purpose.slice";
import DataPurposeForm, {
  DataPurposeFormValues,
} from "~/features/data-purposes/DataPurposeForm";
import { RTKErrorResult } from "~/types/errors/api";

const EditDataPurposePage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const { fidesKey } = router.query;

  const {
    data: purpose,
    error,
    isLoading,
  } = useGetDataPurposeByKeyQuery(fidesKey as string, {
    skip: !fidesKey,
  });

  const [updateDataPurpose] = useUpdateDataPurposeMutation();

  const handleSubmit = async (values: DataPurposeFormValues) => {
    try {
      await updateDataPurpose({
        fidesKey: values.fides_key,
        ...values,
      }).unwrap();
      message.success(`Data purpose "${values.name}" updated successfully`);
    } catch (err) {
      message.error(getErrorMessage(err as RTKErrorResult["error"]));
    }
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the data purpose"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Data Purposes"
          breadcrumbItems={[
            {
              title: "All data purposes",
              href: DATA_PURPOSES_ROUTE,
            },
            {
              title: purpose?.name ?? "Data Purpose",
            },
          ]}
        />
      </SidePanel>
      <Layout title={purpose?.name ?? "Data Purpose"}>
        {isLoading ? (
          <Spin />
        ) : (
          <DataPurposeForm purpose={purpose} handleSubmit={handleSubmit} />
        )}
      </Layout>
    </>
  );
};

export default EditDataPurposePage;
