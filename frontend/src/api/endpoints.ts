import { api, request } from "./";

type Response = { output: string };

/** arbitrary endpoint */
export const endpoint1 = (input: string) =>
  request<Response>(`${api}/endpoint1`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

/** arbitrary endpoint */
export const endpoint2 = (input: string) =>
  request<Response>(`${api}/endpoint2`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

/** arbitrary endpoint */
export const endpoint3 = (input: string) =>
  request<Response>(`${api}/endpoint3`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });
