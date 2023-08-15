import { transformTaxonomyEntityToNodes } from "~/features/taxonomy/helpers";
import { MOCK_DATA_CATEGORIES, MOCK_DATA_SUBJECTS } from "~/mocks/data";

describe("data category transform", () => {
  it("should convert a list of dot strings to nodes", () => {
    const nodes = transformTaxonomyEntityToNodes(MOCK_DATA_CATEGORIES);
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
                is_default: true,
                active: true,
              },
            ],
            description: "Contact data related to a system account.",
            label: "Account Contact Data",
            value: "account.contact",
            is_default: true,
            active: true,
          },
        ],
        description: "Data related to a system account.",
        label: "Account Data",
        value: "account",
        is_default: true,
        active: true,
      },
      {
        children: [
          {
            children: [],
            description: "Data used to manage access to the system.",
            label: "Authentication Data",
            value: "system.authentication",
            is_default: true,
            active: true,
          },
        ],
        description: "Data unique to, and under control of the system.",
        label: "System Data",
        value: "system",
        is_default: true,
        active: true,
      },
      {
        children: [
          {
            children: [],
            description:
              "Data derived from user provided data or as a result of user actions in the system.",
            label: "Derived Data",
            value: "user.derived",
            is_default: true,
            active: true,
          },
          {
            children: [
              {
                children: [],
                description:
                  "Data provided or created directly by a user that is not identifiable.",
                label: "User Provided Non-Identifiable Data",
                value: "user.provided.nonidentifiable",
                is_default: true,
                active: true,
              },
              {
                children: [
                  {
                    children: [],
                    description: "Age range data.",
                    label: "User Provided Non-Specific Age",
                    value: "user.provided.identifiable.non_specific_age",
                    is_default: true,
                    active: true,
                  },
                  {
                    children: [],
                    description:
                      "Data related to the individual's political opinions.",
                    label: "Political Opinion",
                    value: "user.provided.identifiable.political_opinion",
                    is_default: true,
                    active: true,
                  },
                ],
                description:
                  "Data provided or created directly by a user that is linked to or identifies a user.",
                label: "User Provided Identifiable Data",
                value: "user.provided.identifiable",
                is_default: true,
                active: true,
              },
            ],
            description:
              "Data provided or created directly by a user of the system.",
            label: "User Provided Data",
            value: "user.provided",
            is_default: true,
            active: true,
          },
        ],
        description:
          "Data related to the user of the system, either provided directly or derived based on their usage.",
        label: "User Data",
        value: "user",
        is_default: true,
        active: true,
      },
    ]);
  });

  it("should handle items without parent keys as just a flat list", () => {
    const nodes = transformTaxonomyEntityToNodes(MOCK_DATA_SUBJECTS);
    expect(nodes).toEqual([
      {
        label: "Anonymous User",
        value: "anonymous_user",
        description:
          "An individual that is unidentifiable to the systems. Note - This should only be applied to truly anonymous users where there is no risk of re-identification",
        is_default: true,
        children: [],
        active: true,
      },
      {
        label: "Citizen Voter",
        value: "citizen_voter",
        description:
          "An individual registered to voter with a state or authority.",
        is_default: true,
        children: [],
        active: true,
      },
      {
        label: "Commuter",
        value: "commuter",
        description:
          "An individual that is traveling or transiting in the context of location tracking.",
        is_default: true,
        children: [],
        active: true,
      },
    ]);
  });
});
