import { transformCategoriesToNodes } from "./helpers";

describe("transformCategoriesToNodes", () => {
  it("works with a simple example", () => {
    expect(
      transformCategoriesToNodes([
        "grand",
        "grand.parent",
        "grand.parent.child",
        "grand.parent.sibling",
        "grand.sibling",
        "orphan.child",
      ])
    ).toEqual([
      {
        label: "grand",
        value: "grand",
        children: [
          {
            label: "parent",
            value: "grand.parent",
            children: [
              {
                label: "child",
                value: "grand.parent.child",
                children: [],
              },
              {
                label: "sibling",
                value: "grand.parent.sibling",
                children: [],
              },
            ],
          },
          {
            label: "sibling",
            value: "grand.sibling",
            children: [],
          },
        ],
      },
      {
        label: "orphan",
        value: "orphan",
        children: [
          {
            label: "child",
            value: "orphan.child",
            children: [],
          },
        ],
      },
    ]);
  });

  it("uses the category names when provided", () => {
    expect(
      transformCategoriesToNodes(
        ["parent", "parent.child", "anon.orphan"],
        new Map([
          [
            "parent",
            {
              fides_key: "parent",
              name: "Doctor Parent, PhD",
            },
          ],
          [
            "parent.child",
            {
              fides_key: "parent.child",
              name: "Please, call me Child.",
            },
          ],
          [
            "anon.orphan",
            {
              fides_key: "anon.orphan",
              name: "My parent has no name",
            },
          ],
        ])
      )
    ).toEqual([
      {
        label: "Doctor Parent, PhD",
        value: "parent",
        children: [
          {
            label: "Please, call me Child.",
            value: "parent.child",
            children: [],
          },
        ],
      },
      {
        label: "anon",
        value: "anon",
        children: [
          {
            label: "My parent has no name",
            value: "anon.orphan",
            children: [],
          },
        ],
      },
    ]);
  });

  it("works with a real-world example", () => {
    const categoryKeys = [
      "system.operations",
      "system",
      "user.contact.address.state",
      "user.contact.email",
      "user.contact",
      "user.derived.identifiable.device.device_id",
      "user.device.cookie_id",
      "user.device.cookie_id",
      "user.name",
      "user.unique_id",
    ];

    expect(transformCategoriesToNodes(categoryKeys)).toEqual([
      {
        label: "system",
        value: "system",
        children: [
          {
            label: "operations",
            value: "system.operations",
            children: [],
          },
        ],
      },
      {
        label: "user",
        value: "user",
        children: [
          {
            label: "contact",
            value: "user.contact",
            children: [
              {
                label: "address",
                value: "user.contact.address",
                children: [
                  {
                    label: "state",
                    value: "user.contact.address.state",
                    children: [],
                  },
                ],
              },
              {
                label: "email",
                value: "user.contact.email",
                children: [],
              },
            ],
          },
          {
            label: "derived",
            value: "user.derived",
            // 'user.derived.identifiable.device.device_id',
            children: [
              {
                label: "identifiable",
                value: "user.derived.identifiable",
                children: [
                  {
                    label: "device",
                    value: "user.derived.identifiable.device",
                    children: [
                      {
                        label: "device_id",
                        value: "user.derived.identifiable.device.device_id",
                        children: [],
                      },
                    ],
                  },
                ],
              },
            ],
          },
          {
            label: "device",
            value: "user.device",
            children: [
              {
                label: "cookie_id",
                value: "user.device.cookie_id",
                children: [],
              },
            ],
          },
          {
            label: "name",
            value: "user.name",
            children: [],
          },
          {
            label: "unique_id",
            value: "user.unique_id",
            children: [],
          },
        ],
      },
    ]);
  });
});
