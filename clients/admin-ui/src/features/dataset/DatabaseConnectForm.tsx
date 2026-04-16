import {
  Button,
  Flex,
  Form,
  Input,
  Switch,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";
import { useDispatch } from "react-redux";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { DATASET_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import { useCreateClassifyInstanceMutation } from "~/features/plus/plus.slice";
import { Dataset, GenerateTypes, System, ValidTargets } from "~/types/api";

import {
  setActiveDatasetFidesKey,
  useCreateDatasetMutation,
  useGenerateDatasetMutation,
} from "./dataset.slice";

const { Text } = Typography;

const isDataset = (sd: System | Dataset): sd is Dataset =>
  !("system_type" in sd);

interface FormValues {
  url: string;
  classify: boolean;
}

export const DatabaseConnectForm = () => {
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [generateMutation, { isLoading: isGenerating }] =
    useGenerateDatasetMutation();
  const [createMutation, { isLoading: isCreating }] =
    useCreateDatasetMutation();
  const [classifyMutation, { isLoading: isClassifying }] =
    useCreateClassifyInstanceMutation();
  const isLoading = isGenerating || isCreating || isClassifying;

  const message = useMessage();
  const router = useRouter();
  const features = useFeatures();
  const dispatch = useDispatch();
  const confirmModal = useModal();

  const generate = async (
    values: FormValues,
  ): Promise<{ error: string } | { datasets: Dataset[] }> => {
    const result = await generateMutation({
      organization_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      generate: {
        config: { connection_string: values.url },
        target: ValidTargets.DB,
        type: GenerateTypes.DATASETS,
      },
    });

    if (isErrorResult(result)) {
      return { error: getErrorMessage(result.error) };
    }

    const datasets = (result.data.generate_results ?? []).filter(isDataset);
    if (!(datasets && datasets.length > 0)) {
      return { error: "Unable to generate a dataset with this connection." };
    }

    return { datasets };
  };

  const create = async (
    datasetBody: Dataset,
  ): Promise<{ error: string } | { dataset: Dataset }> => {
    const result = await createMutation(datasetBody);

    if (isErrorResult(result)) {
      return { error: getErrorMessage(result.error) };
    }

    return { dataset: result.data };
  };

  const classify = async ({
    values,
    datasets,
  }: {
    values: FormValues;
    datasets: Dataset[];
  }): Promise<
    { error: string } | { classifyInstances: Record<string, string>[] }
  > => {
    const result = await classifyMutation({
      dataset_schemas: datasets.map(({ name, fides_key }) => ({
        fides_key,
        name,
      })),
      schema_config: {
        organization_key: DEFAULT_ORGANIZATION_FIDES_KEY,
        generate: {
          config: { connection_string: values.url },
          target: ValidTargets.DB,
          type: GenerateTypes.DATASETS,
        },
      },
    });

    if (isErrorResult(result)) {
      return { error: getErrorMessage(result.error) };
    }

    return { classifyInstances: result.data.classify_instances };
  };

  const doSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      const generateResult = await generate(values);
      if ("error" in generateResult) {
        message.error(generateResult.error);
        return;
      }

      // Usually only one dataset needs to be created, but create them all just in case.
      const createResults = await Promise.all(
        generateResult.datasets.map((dataset) => create(dataset)),
      );
      const createResult =
        createResults.find((result) => "error" in result) ?? createResults[0];
      if ("error" in createResult) {
        message.error(createResult.error);
        return;
      }

      // Default generate flow:
      if (!values.classify) {
        message.success(`Generated ${createResult.dataset.name} dataset`);
        router.push({
          pathname: DATASET_DETAIL_ROUTE,
          query: { datasetId: createResult.dataset.fides_key },
        });
        return;
      }

      // Additional steps when using classify:
      const classifyResult = await classify({
        values,
        datasets: generateResult.datasets,
      });
      if ("error" in classifyResult) {
        message.error(classifyResult.error);
        return;
      }

      message.success(`Generate and classify are now in progress`);
      dispatch(setActiveDatasetFidesKey(createResult.dataset.fides_key));
      router.push(`/dataset`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinish = async (values: FormValues) => {
    if (values.classify) {
      confirmModal.confirm({
        title: "Generate and classify this dataset",
        content:
          "You have chosen to generate and classify this dataset. This process may take several minutes. In the meantime you can continue using Fides. You will receive a notification when the process is complete.",
        centered: true,
        icon: null,
        onOk: () => doSubmit(values),
      });
    } else {
      await doSubmit(values);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{ url: "", classify: features.plus }}
      onFinish={handleFinish}
      validateTrigger="onSubmit"
    >
      <Flex vertical align="flex-start" gap={32}>
        <Text>
          Connect to a database using the connection URL. You may have received
          this URL from a colleague or your Ethyca developer support engineer.
        </Text>
        <Form.Item
          name="url"
          label="Database URL"
          rules={[{ required: true, message: "Database URL is required" }]}
          className="w-full"
        >
          <Input data-testid="input-url" />
        </Form.Item>

        {features.plus ? (
          <Form.Item
            name="classify"
            layout="horizontal"
            colon={false}
            valuePropName="checked"
            label={
              <Flex align="center" gap="small">
                Classify dataset
                <InfoTooltip label="Use Fides Classify to suggest labels based on your data." />
              </Flex>
            }
          >
            <Switch size="small" data-testid="input-classify" />
          </Form.Item>
        ) : null}

        <Button
          type="primary"
          htmlType="submit"
          loading={isSubmitting || isLoading}
          disabled={isSubmitting || isLoading}
          data-testid="create-dataset-btn"
        >
          Generate dataset
        </Button>
      </Flex>
    </Form>
  );
};
