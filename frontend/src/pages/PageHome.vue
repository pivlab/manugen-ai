<template>
  <EditorContent
    :editor="editor"
    class="editor flex w-full max-w-4xl bg-slate-50 rounded-lg ring-1 ring-slate-500 focus-within:ring-4 focus-within:ring-indigo-500 leading-8 tracking-wide transition-all"
  />

  <FloatingMenu
    v-if="editor"
    :editor="editor"
    class="menu"
    :tippy-options="tippyOptions"
  >
    <template
      v-for="({ icon, label, action, color, cursor }, index) in actions"
      :key="index"
    >
      <button v-if="cursor" class="menu-button" :class="color" @click="action">
        <component :is="icon" />{{ label }}
      </button>
    </template>
  </FloatingMenu>

  <BubbleMenu
    v-if="editor"
    :editor="editor"
    class="menu"
    :tippy-options="tippyOptions"
  >
    <template
      v-for="({ icon, label, action, color, selection }, index) in actions"
      :key="index"
    >
      <button
        v-if="selection"
        class="menu-button"
        :class="color"
        @click="action"
      >
        <component :is="icon" />{{ label }}
      </button>
    </template>
  </BubbleMenu>

  <div class="fixed top-0 left-0">
    <AppAgents />
  </div>

  <div class="fixed left-0 bottom-0 flex p-5 gap-2">
    <AppButton @click="editor?.commands.undo()"><Undo /></AppButton>
    <AppButton @click="editor?.commands.redo()"><Redo /></AppButton>
  </div>

  <div class="fixed right-0 bottom-0 flex p-5 gap-2">
    <AppUpload
      tooltip="Upload document, or drag & drop onto page"
      :accept="accept"
      @files="(files) => editor?.commands.setContent(files[0]?.text ?? '')"
    />
    <AppButton
      @click="downloadTxt(editor?.getText() ?? '', `${title} Document`)"
    >
      <Download />
    </AppButton>
  </div>
</template>

<script setup lang="ts">
import type { ComponentInstance } from "vue";
import {
  useEditor,
  BubbleMenu,
  EditorContent,
  FloatingMenu,
} from "@tiptap/vue-3";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import AppAgents from "@/components/AppAgents.vue";
import AppUpload from "@/components/AppUpload.vue";
import AppButton from "@/components/AppButton.vue";
import {
  Download,
  Feather,
  Paperclip,
  Redo,
  Send,
  Undo,
} from "lucide-vue-next";
import { downloadTxt } from "@/util/download";
import { agents, useAgentAction } from "@/api/agents";
import { endpoint1, endpoint2, endpoint3 } from "@/api/endpoints";

const { VITE_TITLE: title } = import.meta.env;

const editor = useEditor({
  content: "",
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: "Start writing" }),
  ],
  editorProps: {
    attributes: {
      class: "w-full h-full p-10 prose-lg focus:outline-none",
    },
  },
});

const action1 = useAgentAction("gemini", () => endpoint1("1"));
const action2 = useAgentAction("chatgpt", () => endpoint2("2"));
const action3 = useAgentAction("claude", () => endpoint3("3"));

const actions = [
  {
    icon: Feather,
    label: "Action 1",
    action: () => action1().then(console.log),
    color: agents.value.gemini.color,
    selection: true,
    cursor: true,
  },
  {
    icon: Paperclip,
    label: "Action 2",
    action: () => action2().then(console.log),
    color: agents.value.chatgpt.color,
    selection: false,
    cursor: true,
  },
  {
    icon: Send,
    label: "Action 3",
    action: () => action3().then(console.log),
    color: agents.value.claude.color,
    selection: true,
    cursor: false,
  },
];

const accept = [
  ".txt",
  ".doc",
  ".docx",
  ".pdf",
  "text/plain",
  "application/pdf",
  "application/msword",
];

type TippyOptions = ComponentInstance<
  typeof BubbleMenu
>["$props"]["tippyOptions"];

const tippyOptions: TippyOptions = { placement: "bottom" };
</script>

<style>
.tiptap p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

@reference "@/styles.css";

.menu {
  @apply flex gap-2 p-2;
}

.menu-button {
  @apply flex items-center gap-2 px-2 rounded-sm hover:bg-slate-500 transition-all;
}
</style>
