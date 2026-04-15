import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { DATA_PURPOSES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useCreateDataPurposeMutation } from "~/features/data-purposes/data-purpose.slice";
import DataPurposeForm, {
  DataPurposeFormValues,
} from "~/features/data-purposes/DataPurposeForm";
import { RTKErrorResult } from "~/types/errors/api";

const AddDataPurposePage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const [createDataPurpose] = useCreateDataPurposeMutation();

  const handleSubmit = async (values: DataPurposeFormValues) => {
    try {
      await createDataPurpose(values).unwrap();
      message.success(`Purpose "${values.name}" created successfully`);
      router.push(DATA_PURPOSES_ROUTE);
    } catch (error) {
      message.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  return (
    <Layout title="Add purpose">
      <PageHeader
        heading="Purposes"
        breadcrumbItems={[
          {
            title: "All purposes",
            href: DATA_PURPOSES_ROUTE,
          },
          {
            title: "Add purpose",
          },
        ]}
      />
      <div style={{ maxWidth: 720 }}>
        <DataPurposeForm handleSubmit={handleSubmit} />
      </div>
    </Layout>
  );
};

export default AddDataPurposePage;
