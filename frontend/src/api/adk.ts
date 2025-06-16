/*
contains ADK-specific types and utility functions
*/

import { api, request } from "./"

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

type ADKSessionResponse = {
    "id": string,
    "appName": string,
    "userId": string,
    [key: string]: any
}

/**
 *  ensures that a session exists for the current user
 */
export const ensureSessionExists = async (appName: string, userId: string, sessionId : string|null) => {
  // perform GET for the session
  try {
    const result = await fetch(`${api}/adk_api/apps/${appName}/users/${userId}/sessions/${sessionId}`)
    // check that result is not 200 OK
    // this will immediately be caught below to attempt to create a new session
    if (!result.ok) {
      throw new Error(`Session for app ${appName} and user ${userId} does not exist`);
    }
    // if it is 200 OK, return the session
    return await result.json() as ADKSessionResponse;
  }
  catch (e) {
    // if it fails, create a new session
    const createResponse = await fetch(`${api}/adk_api/apps/${appName}/users/${userId}/sessions/${sessionId}`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        "state": {}
      }),
    });

    if (!createResponse.ok) {
      throw new Error(`Failed to create session for app ${appName} and user ${userId}`);
    }

    return await createResponse.json() as ADKSessionResponse;
  }
}

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
