/* eslint-disable no-console */
/* eslint-disable jsx-a11y/label-has-associated-control */
import {
  AntLayout as Layout,
  AntRow as Row,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
  AntTypography as Typography,
} from "fidesui";

import { AntFormPOC } from "./form-experiments/AntForm";
import { FormikAntFormItemPOC } from "./form-experiments/FormikAntFormItem";
import { FormikControlledPOC } from "./form-experiments/FormikControlled";
import { FormikFieldPOC } from "./form-experiments/FormikField";
import { FormikSpreadFieldPOC } from "./form-experiments/FormikSpreadField";

const { Content } = Layout;
const { Title } = Typography;

const items: TabsProps["items"] = [
  {
    key: "1",
    label: "Formik + Controlled",
    children: <FormikControlledPOC />,
  },
  {
    key: "2",
    label: "Formik + Field",
    children: <FormikFieldPOC />,
  },
  {
    key: "3",
    label: "Formik + {...field}",
    children: <FormikSpreadFieldPOC />,
  },
  {
    key: "4",
    label: "Formik + Ant's Form.Item",
    children: <FormikAntFormItemPOC />,
  },
  {
    key: "5",
    label: "Ant Form",
    children: <AntFormPOC />,
  },
];

export const FormsPOC = () => {
  return (
    <Content className="overflow-auto px-10 py-6">
      <Row>
        <Title>Forms POC</Title>
      </Row>
      <Tabs defaultActiveKey="1" items={items} />
    </Content>
  );
};

export default FormsPOC;
