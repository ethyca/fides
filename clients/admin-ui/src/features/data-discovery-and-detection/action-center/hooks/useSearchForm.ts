import { Form, FormProps } from "fidesui";
import { useQueryStates, UseQueryStatesKeysMap, Values } from "nuqs";

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
  const onFieldsChange: FormProps<Values<QueryState>>["onFieldsChange"] = () =>
    form.submit();

  // We are binding the ant form values to nuqs state using the form finished method
  const onFinish: FormProps<Values<QueryState>>["onFinish"] = (values) => {
    const filteredValues = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [
        key,
        value === undefined ? "" : value,
      ]),
    );
    setSearchForm(filteredValues as typeof values);
  };

  return {
    form,
    onFieldsChange,
    onFinish,
    initialValues: {
      ...initialValues,
      ...searchForm,
    },
    requestData: translate(searchForm),
  };
};

export default useSearchForm;
