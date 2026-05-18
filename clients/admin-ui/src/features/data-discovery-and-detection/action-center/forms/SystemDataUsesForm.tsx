import { Form, useMessage } from "fidesui";

import {
  TaxonomySelect,
  TaxonomySelectOption,
} from "~/features/common/dropdown/TaxonomySelect";
import { getErrorMessage } from "~/features/common/helpers";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { isErrorResult } from "~/types/errors";

import { useUpdateInfrastructureSystemDataUsesMutation } from "../../discovery-detection.slice";

type DataUsesForm = {
  dataUses?: string[];
};

export const SystemDataUsesForm = ({
  initialValues,
  monitorId,
  stagedResourceUrn,
}: {
  initialValues: { dataUses: string[] };
  monitorId: string;
  stagedResourceUrn: string;
}) => {
  const messageApi = useMessage();
  const [form] = Form.useForm<DataUsesForm>();
  const dataUsesSelected = Form.useWatch("dataUses", form);
  const [updateDataUses, { isLoading }] =
    useUpdateInfrastructureSystemDataUsesMutation();

  const handleSubmit = async (values: DataUsesForm) =>
    updateDataUses({
      monitorId,
      dataUses: values.dataUses ?? [],
      urn: stagedResourceUrn,
    }).then((result) => {
      if (isErrorResult(result)) {
        messageApi.error(getErrorMessage(result.error));
      }
    });

  const { getDataUseDisplayNameProps, getDataUses } = useTaxonomies();
  const dataUses = getDataUses().filter((use) => use.active);
  const options: TaxonomySelectOption[] = dataUses.map((dataUse) => {
    const { name, primaryName } = getDataUseDisplayNameProps(dataUse.fides_key);

    return {
      value: dataUse.fides_key,
      label: (
        <div>
          <strong>{primaryName || name}</strong>
          {primaryName && `: ${name}`}
        </div>
      ),
      name,
      primaryName,
      description: dataUse.description || "",
    };
  });

  return (
    <Form
      initialValues={initialValues}
      layout="vertical"
      form={form}
      onFieldsChange={() => form.submit()}
      onFinish={handleSubmit}
      className="w-full"
      name="dataUsesForm"
    >
      <Form.Item
        name="dataUses"
        className="m-0"
        initialValue={initialValues.dataUses}
      >
        <TaxonomySelect
          options={options}
          value={dataUsesSelected}
          className="w-full"
          variant="outlined"
          mode="multiple"
          maxTagCount="responsive"
          autoFocus={false}
          loading={isLoading}
        />
      </Form.Item>
    </Form>
  );
};
