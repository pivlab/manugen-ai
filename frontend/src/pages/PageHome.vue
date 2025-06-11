<template>
  <EditorContent
    :editor="editor"
    class="editor flex w-full max-w-4xl bg-slate-50 rounded-lg ring-1 ring-slate-500 focus-within:ring-4 focus-within:ring-indigo-500 leading-8 tracking-wide transition-all"
  />

  <div class="fixed top-0 left-0">
    <AppAgents />
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
import { useEditor, EditorContent } from "@tiptap/vue-3";
import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import AppAgents from "../components/AppAgents.vue";
import AppUpload from "../components/AppUpload.vue";
import AppButton from "../components/AppButton.vue";
import { Download } from "lucide-vue-next";
import { downloadTxt } from "@/util/download";

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

const accept = [
  ".txt",
  ".doc",
  ".docx",
  ".pdf",
  "text/plain",
  "application/pdf",
  "application/msword",
];
</script>

<style>
.tiptap p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
