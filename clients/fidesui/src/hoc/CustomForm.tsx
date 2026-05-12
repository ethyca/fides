import type { FormInstance, FormProps } from "antd/lib";
import { Form } from "antd/lib";
import React from "react";

import { InformationFilled } from "../icons/carbon";

const DEFAULT_TOOLTIP_ICON = (
  <InformationFilled color="var(--fidesui-neutral-200)" />
);

/**
 * Higher-order component that adds a default tooltip icon to Ant Design's Form component.
 *
 * All Form.Item tooltips will use the InformationFilled icon by default,
 * removing the need to pass the icon manually on every Form.Item.
 *
 * The default can be overridden per-Form via the `tooltip` prop or per-Item
 * via `Form.Item tooltip={{ icon: <SomeOtherIcon /> }}`.
 */
const CustomFormBase = <Values = unknown,>(
  props: React.PropsWithChildren<FormProps<Values>> &
    React.RefAttributes<FormInstance<Values>>,
) => {
  const { tooltip, ...rest } = props;
  return (
    <Form<Values>
      tooltip={{ icon: DEFAULT_TOOLTIP_ICON, ...tooltip }}
      {...rest}
    />
  );
};

CustomFormBase.displayName = "CustomForm";

type CustomFormType = typeof CustomFormBase & {
  Item: typeof Form.Item;
  List: typeof Form.List;
  ErrorList: typeof Form.ErrorList;
  Provider: typeof Form.Provider;
  useForm: typeof Form.useForm;
  useFormInstance: typeof Form.useFormInstance;
  useWatch: typeof Form.useWatch;
};

export const CustomForm = CustomFormBase as CustomFormType;
CustomForm.Item = Form.Item;
CustomForm.List = Form.List;
CustomForm.ErrorList = Form.ErrorList;
CustomForm.Provider = Form.Provider;
CustomForm.useForm = Form.useForm;
CustomForm.useFormInstance = Form.useFormInstance;
CustomForm.useWatch = Form.useWatch;
