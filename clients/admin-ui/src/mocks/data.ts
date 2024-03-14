import {
  Classification,
  ClassificationStatus,
  ClassifyCollection,
  ClassifyDataset,
  ClassifyField,
  Dataset,
  DatasetCollection,
  DatasetField,
  System,
} from "~/types/api";

/**
 * Returns a mock system object. Can override default values by
 * passing in a Partial<System>
 */
export const mockSystem = (partialSystem?: Partial<System>): System => {
  const system: System = {
    system_type: "Service",
    privacy_declarations: [],
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
    is_default: true,
    active: true,
  },
  {
    description: "Data related to the individual's political opinions.",
    fides_key: "user.provided.identifiable.political_opinion",
    name: "Political Opinion",
    organization_fides_key: "default_organization",
    parent_key: "user.provided.identifiable",
    is_default: true,
    active: true,
  },
  {
    description:
      "Data provided or created directly by a user that is not identifiable.",
    fides_key: "user.provided.nonidentifiable",
    name: "User Provided Non-Identifiable Data",
    organization_fides_key: "default_organization",
    parent_key: "user.provided",
    is_default: true,
    active: true,
  },
  {
    description: "Data related to a system account.",
    fides_key: "account",
    name: "Account Data",
    organization_fides_key: "default_organization",
    parent_key: null,
    is_default: true,
    active: true,
  },
  {
    description: "Contact data related to a system account.",
    fides_key: "account.contact",
    name: "Account Contact Data",
    organization_fides_key: "default_organization",
    parent_key: "account",
    is_default: true,
    active: true,
  },
  {
    description: "Account's city level address data.",
    fides_key: "account.contact.city",
    name: "Account City",
    organization_fides_key: "default_organization",
    parent_key: "account.contact",
    is_default: true,
    active: true,
  },
  {
    description: "Data unique to, and under control of the system.",
    fides_key: "system",
    name: "System Data",
    organization_fides_key: "default_organization",
    parent_key: null,
    is_default: true,
    active: true,
  },
  {
    description: "Data used to manage access to the system.",
    fides_key: "system.authentication",
    name: "Authentication Data",
    organization_fides_key: "default_organization",
    parent_key: "system",
    is_default: true,
    active: true,
  },
  {
    description:
      "Data related to the user of the system, either provided directly or derived based on their usage.",
    fides_key: "user",
    name: "User Data",
    organization_fides_key: "default_organization",
    parent_key: null,
    is_default: true,
    active: true,
  },
  {
    description:
      "Data derived from user provided data or as a result of user actions in the system.",
    fides_key: "user.derived",
    name: "Derived Data",
    organization_fides_key: "default_organization",
    parent_key: "user",
    is_default: true,
    active: true,
  },
  {
    description: "Data provided or created directly by a user of the system.",
    fides_key: "user.provided",
    name: "User Provided Data",
    organization_fides_key: "default_organization",
    parent_key: "user",
    is_default: true,
    active: true,
  },
  {
    description:
      "Data provided or created directly by a user that is linked to or identifies a user.",
    fides_key: "user.provided.identifiable",
    name: "User Provided Identifiable Data",
    organization_fides_key: "default_organization",
    parent_key: "user.provided",
    is_default: true,
    active: true,
  },
];

export const MOCK_DATA_SUBJECTS = [
  {
    fides_key: "anonymous_user",
    organization_fides_key: "default_organization",
    tags: null,
    name: "Anonymous User",
    description:
      "An individual that is unidentifiable to the systems. Note - This should only be applied to truly anonymous users where there is no risk of re-identification",
    rights: null,
    automated_decisions_or_profiling: null,
    is_default: true,
    active: true,
  },
  {
    fides_key: "citizen_voter",
    organization_fides_key: "default_organization",
    tags: null,
    name: "Citizen Voter",
    description: "An individual registered to voter with a state or authority.",
    rights: null,
    automated_decisions_or_profiling: null,
    is_default: true,
    active: true,
  },
  {
    fides_key: "commuter",
    organization_fides_key: "default_organization",
    tags: null,
    name: "Commuter",
    description:
      "An individual that is traveling or transiting in the context of location tracking.",
    rights: null,
    automated_decisions_or_profiling: null,
    is_default: true,
    active: true,
  },
];

export const mockDatasetField = (
  partialField?: Partial<DatasetField>
): DatasetField => {
  const field: DatasetField = {
    name: "created_at",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
  };
  return Object.assign(field, partialField);
};

export const mockDatasetCollection = (
  partialCollection?: Partial<DatasetCollection>
): DatasetCollection => {
  const collection: DatasetCollection = {
    name: "created_at",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
    fields: [mockDatasetField()],
  };
  return Object.assign(collection, partialCollection);
};

export const mockDataset = (partialDataset?: Partial<Dataset>): Dataset => {
  const dataset: Dataset = {
    fides_key: "sample_dataset",
    organization_fides_key: "mock_organization",
    name: "created_at",
    description: "User's creation timestamp",
    data_categories: ["system.operations"],
    collections: [mockDatasetCollection()],
  };
  return Object.assign(dataset, partialDataset);
};

export const mockClassification = (
  partial?: Partial<Classification>
): Classification => {
  const initial: Classification = {
    label: "system.operations",
    score: 1,
    aggregated_score: 1,
    classification_paradigm: "",
  };
  return Object.assign(initial, partial);
};

export const mockClassifyField = (
  partial?: Partial<ClassifyField>
): ClassifyField => {
  const initial: ClassifyField = {
    name: "created_at",
    classifications: [mockClassification()],
  };
  return Object.assign(initial, partial);
};

export const mockClassifyCollection = (
  partial?: Partial<ClassifyCollection>
): ClassifyCollection => {
  const initial: ClassifyCollection = {
    name: "created_at",
    fields: [mockClassifyField()],
  };
  return Object.assign(initial, partial);
};

export const mockClassifyDataset = (
  partial?: Partial<ClassifyDataset>
): ClassifyDataset => {
  const initial: ClassifyDataset = {
    fides_key: "sample_dataset",
    name: "sample_dataset",
    status: ClassificationStatus.COMPLETE,
    collections: [mockClassifyCollection()],
  };
  return Object.assign(initial, partial);
};
