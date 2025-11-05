import {
  AntAvatar as Avatar,
  AntDescriptions as Descriptions,
  AntFlex as Flex,
  AntForm as Form,
  AntList as List,
  AntParagraph as Paragraph,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
  Icons,
  SparkleIcon,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { ClassifierProgress } from "~/features/classifier/ClassifierProgress";
import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";

import { DetailsDrawer } from "./DetailsDrawer";
import { DetailsDrawerProps } from "./DetailsDrawer/types";
import { ACTION_ALLOWED_STATUSES } from "./FieldActions.const";
import { MonitorResource } from "./types";
import { useFieldActions } from "./useFieldActions";

interface ResourceDetailsDrawerProps extends DetailsDrawerProps {
  resource?: MonitorResource;
  /** TODO: would be nice to have generic action/forms available native with details drawer */
  fieldActions: ReturnType<typeof useFieldActions>;
}

const renderTabBar: TabsProps["renderTabBar"] = (props, DefaultTabBar) => (
  <DefaultTabBar {...props} className="!sticky top-0 z-[2] bg-white" />
);

export const ResourceDetailsDrawer = ({
  resource,
  fieldActions,
  ...drawerProps
}: ResourceDetailsDrawerProps) => {
  return (
    <DetailsDrawer
      {...drawerProps}
      classNames={{
        body: "!pt-0 !mt-[var(--ant-padding-lg)] max-h-full",
      }}
    >
      {resource ? (
        <Tabs
          defaultActiveKey="details"
          renderTabBar={renderTabBar}
          items={[
            {
              key: "details",
              label: "Details",
              children: (
                <Flex gap="middle" vertical>
                  <Descriptions
                    bordered
                    size="small"
                    column={1}
                    items={[
                      {
                        key: "system",
                        label: "System",
                        children: resource.system_key,
                      },
                      {
                        key: "path",
                        label: "Path",
                        children: resource.urn,
                      },
                      {
                        key: "data-type",
                        label: "Data type",
                        children:
                          resource.resource_type /** data type is not yet returned from the BE for the details query * */,
                      },
                      {
                        key: "description",
                        label: "Description",
                        children: resource.description,
                      },
                    ]}
                  />
                  <Form layout="vertical">
                    <Form.Item label="Data categories">
                      <DataCategorySelect
                        variant="outlined"
                        mode="multiple"
                        maxTagCount="responsive"
                        value={[
                          ...(resource.classifications?.map(
                            ({ label }) => label,
                          ) ?? []),
                          ...(resource.user_assigned_data_categories?.map(
                            (value) => value,
                          ) ?? []),
                        ]}
                        autoFocus={false}
                        disabled={
                          resource?.diff_status
                            ? !ACTION_ALLOWED_STATUSES[
                                "assign-categories"
                              ].some(
                                (status) => status === resource.diff_status,
                              )
                            : true
                        }
                        onChange={(values) =>
                          fieldActions["assign-categories"]([resource.urn], {
                            user_assigned_data_categories: values,
                          })
                        }
                      />
                    </Form.Item>
                  </Form>
                  {resource.classifications &&
                    resource.classifications.length > 0 && (
                      <List
                        dataSource={resource.classifications}
                        renderItem={(item) => (
                          <List.Item>
                            <List.Item.Meta
                              avatar={
                                <Avatar
                                  /* Ant only provides style prop for altering the background color */
                                  style={{
                                    backgroundColor:
                                      palette?.FIDESUI_BG_DEFAULT,
                                  }}
                                  icon={<SparkleIcon color="black" />}
                                />
                              }
                              title={
                                <Flex align="center" gap="middle">
                                  <div>{item.label}</div>
                                  <ClassifierProgress
                                    percent={item.score * 100}
                                  />
                                </Flex>
                              }
                              description={item.rationale}
                            />
                          </List.Item>
                        )}
                      />
                    )}
                </Flex>
              ),
            },
            {
              key: "activity",
              label: "Activity",
              children: (
                <List
                  dataSource={
                    "errors" in resource && resource.errors
                      ? resource.errors?.map((error, i) => ({
                          key: i,
                          title: error.phase,
                          description: new Date(
                            error.timestamp,
                          ).toLocaleString(),
                          content: error.message,
                        }))
                      : [...Array(20)].map(() => ({
                          title: "test%est test ",
                          description: "ttsjsjsjsj",
                          content: [...Array(25)]
                            .map(() => "error error, ")
                            .join(),
                        }))
                  }
                  renderItem={(item, index) => (
                    <List.Item key={index}>
                      <List.Item.Meta
                        title={item.title}
                        description={item.description}
                      />
                      <Paragraph
                        ellipsis={{
                          expandable: "collapsible",
                          rows: 3,
                        }}
                        copyable={{
                          icon: <Icons.Copy className="pt-1" size={18} />,
                        }}
                      >
                        {item.content}
                      </Paragraph>
                    </List.Item>
                  )}
                  itemLayout="vertical"
                />
              ),
            },
          ]}
        />
      ) : null}
    </DetailsDrawer>
  );
};
