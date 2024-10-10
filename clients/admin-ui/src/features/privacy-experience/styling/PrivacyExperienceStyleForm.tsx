import {
  AntButton as Button,
  AntCollapse,
  AntColorPicker,
  AntForm,
  AntInput,
  AntInputNumber,
  AntSelect,
  Heading,
} from "fidesui";
import { useFormikContext } from "formik";
import { entries } from "lodash";
import { S } from "msw/lib/glossary-de6278a9";

import { PrivacyExperienceConfigColumnLayout } from "~/features/privacy-experience/PrivacyExperienceForm";
import { ExperienceConfigCreate } from "~/types/api";

import {
  StylableCssPropertiesLabels,
  stylingOptionsAvailable,
} from "./constants";
import { StylableCssPropertiesEnum } from "./types";

const PrivacyExperienceStyleForm = ({
  onReturnToMainForm,
}: {
  onReturnToMainForm: () => void;
}) => {
  const [form] = AntForm.useForm();

  const { setFieldValue } = useFormikContext<
    ExperienceConfigCreate & { css: string }
  >();

  const parseColor = (color: any) => {
    if (!color || color.cleared) {
      return undefined;
    }
    const { r, g, b, a } = color.metaColor;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  };

  const handleValuesChanged = (changed: any, all: any) => {
    console.log("all", all);

    // generate css
    const newCss = entries(all).reduce((acc, [elementId, value]) => {
      const { cssSelector } =
        stylingOptionsAvailable.find(({ id }) => id === elementId) ?? {};

      let newAcc = acc;

      // add css for each property
      if (cssSelector) {
        newAcc += `${cssSelector} { `;
        entries(value).forEach(([property, formValue]) => {
          let propertyValue = formValue;

          if (!propertyValue) {
            return;
          }

          if (
            property === StylableCssPropertiesEnum.paddingTop ||
            property === StylableCssPropertiesEnum.paddingBottom
          ) {
            propertyValue = `${propertyValue}px`;
          }

          if (
            property === StylableCssPropertiesEnum.color ||
            property === StylableCssPropertiesEnum.backgroundColor
          ) {
            propertyValue = parseColor(propertyValue);
          }

          if (property === StylableCssPropertiesEnum.backgroundImage) {
            propertyValue = `url(${propertyValue})`;
          }

          newAcc += `${property}: ${propertyValue};`;
        });
        newAcc += `} `;
      }

      return newAcc;
    }, "");

    console.log("newCss", newCss);
    setFieldValue("css", newCss);
  };

  const buttonPanel = (
    <div className="flex justify-between border-t border-[#DEE5EE] p-4">
      <Button onClick={onReturnToMainForm}>Cancel</Button>
      <Button type="primary">Save</Button>
    </div>
  );

  const renderPropertyInput = (property: string) => {
    switch (property) {
      case StylableCssPropertiesEnum.color:
      case StylableCssPropertiesEnum.backgroundColor:
        return <AntColorPicker format="rgb" />;
      case StylableCssPropertiesEnum.fontSize:
        return (
          <AntSelect
            placeholder="Choose size"
            options={[
              { label: "Small", value: "12px" },
              { label: "Medium", value: "16px" },
              { label: "Large", value: "20px" },
              { label: "Extra Large", value: "26px" },
            ]}
            allowClear
          />
        );
      case StylableCssPropertiesEnum.fontWeight:
        return (
          <AntSelect
            placeholder="Choose font weight"
            options={[
              { label: "Regular", value: "400" },
              { label: "Semi-bold", value: "600" },
              { label: "Bold", value: "700" },
            ]}
            allowClear
          />
        );
      case StylableCssPropertiesEnum.paddingTop:
      case StylableCssPropertiesEnum.paddingBottom:
        return <AntInputNumber placeholder="Enter padding" suffix="px" />;

      case StylableCssPropertiesEnum.backgroundSize:
        return (
          <AntSelect
            placeholder="Choose size"
            options={[
              { label: "Cover", value: "cover" },
              { label: "Contain", value: "contain" },
            ]}
            allowClear
          />
        );

      case StylableCssPropertiesEnum.backgroundRepeat:
        return (
          <AntSelect
            placeholder="Choose repeat"
            options={[
              { label: "No-repeat", value: "no-repeat" },
              { label: "Repeat", value: "repeat" },
              { label: "Repeat-x", value: "repeat-x" },
              { label: "Repeat-y", value: "repeat-y" },
            ]}
            allowClear
          />
        );
      case StylableCssPropertiesEnum.backgroundPosition:
        return (
          <AntSelect
            placeholder="Choose position"
            options={[
              { label: "Top", value: "top" },
              { label: "Center", value: "center" },
              { label: "Bottom", value: "bottom" },
              { label: "Left", value: "left" },
              { label: "Right", value: "right" },
            ]}
            allowClear
          />
        );
      case StylableCssPropertiesEnum.backgroundImage:
        return <AntInput placeholder="Enter image URL" />;

      default:
        return <AntInput />;
    }
  };

  const collapseItems = stylingOptionsAvailable.map(
    ({ id, label, properties }) => ({
      key: label,
      label,
      children: properties.map((property) => (
        <AntForm.Item
          name={[id, property]}
          label={StylableCssPropertiesLabels[property]}
          key={property}
          className="mb-2"
          layout="horizontal"
          labelCol={{ span: 12 }}
          labelAlign="left"
        >
          {renderPropertyInput(property)}
        </AntForm.Item>
      )),
      style: {
        backgroundColor: "transparent",
      },
    }),
  );

  return (
    <PrivacyExperienceConfigColumnLayout buttonPanel={buttonPanel} pt="4">
      <Heading fontSize="md" fontWeight="semibold">
        Edit appearance
      </Heading>
      <AntForm
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChanged}
      >
        <AntCollapse
          accordion
          items={collapseItems}
          bordered={false}
          defaultActiveKey={[]}
          size="small"
          style={{ backgroundColor: "transparent" }}
          expandIconPosition="end"
        />
      </AntForm>
    </PrivacyExperienceConfigColumnLayout>
  );
};

export default PrivacyExperienceStyleForm;
