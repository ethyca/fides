import { transformDataCategoriesToNodes } from "~/features/taxonomy/helpers";

describe("data category transform", () => {
  const categories = [
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
  it("should convert a list of dot strings to nodes", () => {
    const nodes = transformDataCategoriesToNodes(categories);
    expect(nodes).toEqual([
      {
        children: [
          {
            children: [
              {
                children: [],
                description: "Account's city level address data.",
                label: "Account City",
                value: "account.contact.city",
              },
            ],
            description: "Contact data related to a system account.",
            label: "Account Contact Data",
            value: "account.contact",
          },
        ],
        description: "Data related to a system account.",
        label: "Account Data",
        value: "account",
      },
      {
        children: [
          {
            children: [],
            description: "Data used to manage access to the system.",
            label: "Authentication Data",
            value: "system.authentication",
          },
        ],
        description: "Data unique to, and under control of the system.",
        label: "System Data",
        value: "system",
      },
      {
        children: [
          {
            children: [],
            description:
              "Data derived from user provided data or as a result of user actions in the system.",
            label: "Derived Data",
            value: "user.derived",
          },
          {
            children: [
              {
                children: [],
                description:
                  "Data provided or created directly by a user that is not identifiable.",
                label: "User Provided Non-Identifiable Data",
                value: "user.provided.nonidentifiable",
              },
              {
                children: [
                  {
                    children: [],
                    description: "Age range data.",
                    label: "User Provided Non-Specific Age",
                    value: "user.provided.identifiable.non_specific_age",
                  },
                  {
                    children: [],
                    description:
                      "Data related to the individual's political opinions.",
                    label: "Political Opinion",
                    value: "user.provided.identifiable.political_opinion",
                  },
                ],
                description:
                  "Data provided or created directly by a user that is linked to or identifies a user.",
                label: "User Provided Identifiable Data",
                value: "user.provided.identifiable",
              },
            ],
            description:
              "Data provided or created directly by a user of the system.",
            label: "User Provided Data",
            value: "user.provided",
          },
        ],
        description:
          "Data related to the user of the system, either provided directly or derived based on their usage.",
        label: "User Data",
        value: "user",
      },
    ]);
  });
});
