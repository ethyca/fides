import { rest } from "msw";

interface SubjectRequestBody {
  username: string;
}

const mockSubjectRequestPreviewResponse = {
  items: [
    {
      status: "error",
      identity: {
        email: "james.braithwaite@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Sammie_Shanahan@gmail.com",
      id: "123",
    },
    {
      status: "denied",
      identity: {
        phone: "555-325-685-126",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Richmond33@yahoo.com",
      id: "456",
    },
    {
      status: "pending",
      identity: {
        email: "mary.jane.@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Oceane.Volkman@gmail.com",
      id: "789",
    },
    {
      status: "new",
      identity: {
        email: "jeremiah.stones@email.com",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Verdie64@yahoo.com",
      id: "012",
    },
    {
      status: "completed",
      identity: {
        phone: "283-774-5003",
      },
      created_at: "August 4, 2021, 09:35:46 PST",
      reviewed_by: "Maximo_Willms0@gmail.com",
      id: "345",
    },
  ],
};

// eslint-disable-next-line import/prefer-default-export
export const handlers = [
  rest.get<SubjectRequestBody>(
    "http://localhost:8080/api/v1/privacy-request",
    async (req, res, ctx) => {
      // mock loading response
      await new Promise((resolve) => {
        setTimeout(() => resolve(null), 1000);
      });

      return res(ctx.json(mockSubjectRequestPreviewResponse));
    },
  ),
];
