import { Form, FormProps } from "fidesui";
import { useQueryStates, UseQueryStatesKeysMap, Values } from "nuqs";
import { useEffect } from "react";

/**
 * @description links ant form handler with nuqs query state
 */
const useSearchForm = <RequestData, QueryState extends UseQueryStatesKeysMap>({
  queryState,
  initialValues,
  translate,
}: {
  queryState: QueryState;
  initialValues?: Partial<Values<QueryState>>;
  translate: (formData: Values<QueryState>) => RequestData;
}) => {
  const [searchForm, setSearchForm] = useQueryStates(queryState, {
    history: "push",
  });
  const [form] = Form.useForm<Values<QueryState>>();

  // Without a submit button, we want to re-submit on every change
  const onFieldsChange: FormProps<
    Values<QueryState>
  >["onFieldsChange"] = () => {
    const values = form.getFieldsValue(true);
    // Translation of undefined/empty string usage as default values in ant vs nuqs
    const translatedValues = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [
        key,
        value === undefined ? "" : value,
      ]),
    );
    setSearchForm(translatedValues as typeof values);
  };

  // Unfortunate need for effect due to current routing strategy
  useEffect(() => {
    // Translation of undefined/empty string usage as default values in ant vs nuqs
    const translatedValues = Object.fromEntries(
      Object.entries(searchForm).map(([key, value]) => [
        key,
        value === "" ? undefined : value,
      ]),
    );

    form.setFieldsValue(
      translatedValues as Parameters<typeof form.setFieldsValue>[0],
    ); // Casting again due to weird ant types
  }, [searchForm, form]);

  return {
    form,
    onFieldsChange,
    initialValues: {
      ...initialValues,
      ...searchForm,
    },
    requestData: translate(searchForm),
  };
};

export default useSearchForm;
