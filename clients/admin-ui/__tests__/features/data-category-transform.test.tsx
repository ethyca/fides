import { transformDataCategoriesToNodes } from "~/features/taxonomy/helpers";
import { MOCK_DATA_CATEGORIES } from "~/mocks/data";

describe("data category transform", () => {
  it("should convert a list of dot strings to nodes", () => {
    const nodes = transformDataCategoriesToNodes(MOCK_DATA_CATEGORIES);
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
