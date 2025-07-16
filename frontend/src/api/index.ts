/** api base url */
export const api = import.meta.env.VITE_API;

/** generic request */
export const request = async <Response>(
  url: string | URL,
  options: RequestInit = {},
) => {
  /** normalize url to url object */
  url = new URL(url);

  /** create request */
  const request = new Request(url, options);

  /** make request */
  const response = await fetch(request);

  let error = "";

  /** check status */
  if (!response.ok) error = "Response not OK";

  /** try to parse as json */
  let parsed: Response | undefined;
  try {
    parsed = await response.clone().json();
  } catch (e) {
    error = "Couldn't parse response";
  }

  /** catch errors */
  if (error || parsed === undefined) throw Error(error);

  return parsed;
};
