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
import { useMemo } from "react";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import { SeverityGauge } from "~/features/common/progress/SeverityGauge";

import { DetailsDrawer } from "./DetailsDrawer";
import { DetailsDrawerProps } from "./DetailsDrawer/types";
import { ACTION_ALLOWED_STATUSES } from "./FieldActions.const";
import { MonitorResource } from "./types";
import { useFieldActions } from "./useFieldActions";
import { mapConfidenceBucketToSeverity } from "./utils";

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
  const filteredClassifications = useMemo(() => {
    if (!resource?.classifications) {
      return [];
    }
    const preferredDataCategories =
      "preferred_data_categories" in resource
        ? (resource.preferred_data_categories ?? [])
        : [];
    return resource.classifications.filter((classification) =>
      preferredDataCategories.includes(classification.label),
    );
  }, [resource]);

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
                          "source_data_type" in resource
                            ? resource.source_data_type
                            : undefined,
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
                        value={
                          "preferred_data_categories" in resource
                            ? resource.preferred_data_categories
                            : []
                        }
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
                  {filteredClassifications.length > 0 && (
                    <List
                      data-testid="classifications-reasoning-list"
                      dataSource={filteredClassifications}
                      renderItem={(item) => {
                        const severity = item.confidence_bucket
                          ? mapConfidenceBucketToSeverity(
                              item.confidence_bucket,
                            )
                          : undefined;

                        return (
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
                                  {severity && (
                                    <SeverityGauge severity={severity} />
                                  )}
                                </Flex>
                              }
                              description={item.rationale}
                            />
                          </List.Item>
                        );
                      }}
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
                      : []
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
