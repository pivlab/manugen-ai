/*
contains ADK-specific types and utility functions
*/

/*
ADK sends a response from /run or /run_sse back as a list of objects, where each
object represents a set of function invocations, function
responses, and text responses back to the user.
each response is of the following form:
{
  "content": {
    "parts": [{"<type>": <data>}],
    "role": "<role>>"
  },
  ...
}
<type> can  be "text", "functionCall", or "functionResponse"
- for the function types, the <data> payload is an object
  that contains, e.g., the arguments or the return value
- for the text type, the <data> payload is a string
<role> can be "user" or "model", and seems to vary depending on who's
  asking who (e.g. function responses come in with the role "user")
*/
export type ADKResponse = [
    {
        "content": {
            "parts": {[key:string]: any}[],
            "role": string
        },
        "partial": boolean,
        "usageMetadata": {
            "candidatesTokenCount": bigint,
            "promptTokenCount": bigint,
            "totalTokenCount": bigint
        },
        "invocationId": string,
        "author": string,
        "actions": {
            "stateDelta": {
                [key:string]: string
            },
            "artifactDelta": object,
            "requestedAuthConfigs": object
        },
        "id": string,
        "timestamp": number
    }
]

export const extractADKText = (response: ADKResponse, onlyLast: boolean = true): string => {
  const textSections = response
    .map(item => item.content.parts)
    .map(parts => {
      // filter for parts that are of type "text"
      const textParts = parts.filter(part => part.text !== undefined);
      // if there are no text parts, return an empty string
      if (textParts.length === 0) return "";
      // otherwise, return the text of the first text part
      return textParts.map(x => x.text).join("\n");
  })

  if (onlyLast) {
    // if onlyLast is true, return the last text section
    return textSections.length > 0 ? textSections[textSections.length - 1] : "";
  }
  else {
    // if onlyLast is false, return all text sections concatenated
    return textSections.join("\n");
  }
}
