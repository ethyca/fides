import {
  Dataset,
  DatasetCollection,
  DatasetField,
} from "~/features/dataset/types";
import { System } from "~/features/system/types";

/**
 * Returns a mock system object. Can override default values by
 * passing in a Partial<System>
 */
export const mockSystem = (partialSystem?: Partial<System>): System => {
  const system: System = {
    system_type: "Service",
    data_responsibility_title: "Controller",
    privacy_declarations: [],
    data_protection_impact_assessment: { is_required: true },
    fides_key: "analytics_system",
    organization_fides_key: "sample_organization",
  };
  return Object.assign(system, partialSystem);
};

/**
 * Returns a list of mock systems of length `number`
 */
export const mockSystems = (number: number) =>
  Array.from({ length: number }, (_, i) =>
    mockSystem({
      system_type: `Service ${i}`,
      fides_key: `analytics_system_${i}`,
    })
  );

export const MOCK_DATA_CATEGORIES = [
  {
    description: "Age range data.",
    fides_key: "user.provided.identifiable.non_specific_age",
    name: "User Provided Non-Specific Age",
    organization_fides_key: "default_organization",
    parent_key: "user.provided.identifiable",
  },
  {
    description: "Data related to the individual's political opinions.",
    fides_key: "user.provided.identifiable.political_opinion",
    name: "Political Opinion",
    organization_fides_key: "default_organization",
    parent_key: "user.provided.identifiable",
  },
  {
    description:
      "Data provided or created directly by a user that is not identifiable.",
    fides_key: "user.provided.nonidentifiable",
    name: "User Provided Non-Identifiable Data",
    organization_fides_key: "default_organization",
    parent_key: "user.provided",
  },
  {
    description: "Data related to a system account.",
    fides_key: "account",
    name: "Account Data",
    organization_fides_key: "default_organization",
    parent_key: null,
  },
  {
    description: "Contact data related to a system account.",
    fides_key: "account.contact",
    name: "Account Contact Data",
    organization_fides_key: "default_organization",
    parent_key: "account",
  },
  {
    description: "Account's city level address data.",
    fides_key: "account.contact.city",
    name: "Account City",
    organization_fides_key: "default_organization",
    parent_key: "account.contact",
  },
  {
    description: "Data unique to, and under control of the system.",
    fides_key: "system",
    name: "System Data",
    organization_fides_key: "default_organization",
    parent_key: null,
  },
  {
    description: "Data used to manage access to the system.",
    fides_key: "system.authentication",
    name: "Authentication Data",
    organization_fides_key: "default_organization",
    parent_key: "system",
  },
  {
    description:
      "Data related to the user of the system, either provided directly or derived based on their usage.",
    fides_key: "user",
    name: "User Data",
    organization_fides_key: "default_organization",
    parent_key: null,
  },
  {
    description:
      "Data derived from user provided data or as a result of user actions in the system.",
    fides_key: "user.derived",
    name: "Derived Data",
    organization_fides_key: "default_organization",
    parent_key: "user",
  },
  {
    description: "Data provided or created directly by a user of the system.",
    fides_key: "user.provided",
    name: "User Provided Data",
    organization_fides_key: "default_organization",
    parent_key: "user",
  },
  {
    description:
      "Data provided or created directly by a user that is linked to or identifies a user.",
    fides_key: "user.provided.identifiable",
    name: "User Provided Identifiable Data",
    organization_fides_key: "default_organization",
    parent_key: "user.provided",
  },
];

export const mockDatasetField = (
  partialField?: Partial<DatasetField>
): DatasetField => {
  const field: DatasetField = {
    name: "created_at",
    data_qualifier: "aggregated",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
    retention: "Account termination",
  };
  return Object.assign(field, partialField);
};

export const mockDatasetCollection = (
  partialCollection?: Partial<DatasetCollection>
): DatasetCollection => {
  const collection: DatasetCollection = {
    name: "created_at",
    data_qualifier: "aggregated",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
    retention: "Account termination",
    fields: [mockDatasetField()],
  };
  return Object.assign(collection, partialCollection);
};

export const mockDataset = (partialDataset?: Partial<Dataset>): Dataset => {
  const dataset: Dataset = {
    fides_key: "sample_dataset",
    organization_fides_key: "mock_organization",
    name: "created_at",
    data_qualifier: "aggregated",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
    retention: "Account termination",
    collections: [mockDatasetCollection()],
  };
  return Object.assign(dataset, partialDataset);
};
