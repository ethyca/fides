import { Form, FormProps } from "fidesui";
import { useQueryStates, UseQueryStatesKeysMap, Values } from "nuqs";
import { useEffect } from "react";
import { InferOutput, ObjectEntries, ObjectSchema, safeParse } from "valibot";

/** Ugly type matching for now * */
type InferredOutput<
  Output,
  VSchema extends ObjectSchema<ObjectEntries, undefined>,
  NState extends UseQueryStatesKeysMap,
> =
  Output extends InferOutput<ObjectSchema<ObjectEntries, undefined>>
    ? Output extends Values<NState>
      ? {
          schema: VSchema;
          queryState: NState;
        }
      : never
    : never;

/**
 * @description links ant form handler with nuqs query state via valibot
 */
const useSearchForm = <RequestData, FormType>({
  schema /** Ant form validation and types are abysmal. A separate schema validator is necessary to get sane types that can be verified * */,
  queryState,
  initialValues,
  translate,
}: InferredOutput<
  FormType,
  ObjectSchema<ObjectEntries, undefined>,
  UseQueryStatesKeysMap
> & {
  initialValues?: Partial<FormType>;
  translate: (formData: FormType) => RequestData;
}) => {
  const [searchForm, setSearchForm] = useQueryStates(queryState, {
    history: "push",
  });
  const [form] = Form.useForm<FormType>();

  // Without a submit button, we want to re-submit on every change
  const onFieldsChange: FormProps<FormType>["onFieldsChange"] = () =>
    form.submit();

  const onFinish: FormProps<FormType>["onFinish"] = (values) => {
    const { success, output } = safeParse(schema, values);

    if (success) {
      setSearchForm(output);
    }
  };

  // Unfortunate need for effect due to current routin strategy
  useEffect(() => {
    form.setFieldsValue(searchForm);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchForm]);

  return {
    form,
    onFieldsChange,
    onFinish,
    initialValues: {
      ...initialValues,
      ...searchForm,
    },
    requestData: translate(searchForm as FormType),
  };
};

export default useSearchForm;
