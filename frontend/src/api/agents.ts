/** list of agents and their "branding" */
export const agents = {
  gemini: {
    name: "Gemini",
    bgColor: "bg-linear-to-r from-blue-100 to-indigo-100",
    textColor: "text-indigo-700",
  },

  chatgpt: {
    name: "ChatGPT",
    bgColor: "bg-linear-to-r from-green-100 to-emerald-100",
    textColor: "text-emerald-700",
  },

  claude: {
    name: "Claude",
    bgColor: "bg-linear-to-r from-red-100 to-orange-100",
    textColor: "text-orange-700",
  },
};

export type AgentId = keyof typeof agents;
