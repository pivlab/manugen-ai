<template>
  <div class="flex-col">
    <h1 class="text-2xl/7 font-bold text-gray-600 sm:truncate sm:text-3xl sm:tracking-tight">Attachments</h1>

    <div class="flex w-full rounded-full border border-gray-300 p-3">
      <input type="text" class="w-full pl-4" v-model="uploadedFileName" placeholder="Name" />
      <AppUploadArtifact
        tooltip="Upload document, or drag & drop onto page"
        :accept="accept"
        :processing="isProcessing"
        single
        @files="(files) => acceptFiles(files)"
      />
    </div>

    <div class="artifacts flex-grow">
      <AppArtifact v-for="artifact in artifacts" :key="artifact.filename" :artifact="artifact" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps } from "vue";
import AppUploadArtifact from "@/components/AppUploadArtifact.vue";
import AppArtifact from "@/components/AppArtifact.vue";
import { uploadArtifact, extractADKText } from "@/api/adk";
import type { UploadedFile } from "@/util/upload";

const props = defineProps(['session'])

/* stores local list of artifacts */
const artifacts = ref([] as UploadedFile[]);

const isProcessing = ref(false);
const uploadedFileName = ref("");

/** upload file types */
const imageAccepts = [
  ".png",
  ".jpeg",
  ".jpg",
  ".svg",
  "image/png",
  "image/jpeg",
  "image/jpg"
];

const textAccepts = [
  ".txt",
  ".py",
  ".ipynb",
  ".js",
  ".R",
  ".Rmd",
  "text/plain"
];

const accept = [
  ...imageAccepts,
  ...textAccepts
];

const isMimeRoot = (mimetype: string|null, root: string) => {
  return mimetype && mimetype.startsWith(root + "/");
}

const acceptFiles = async (files: any[]) => {
  isProcessing.value = true;

  // for each file, upload it
  try {
      await Promise.all(files.map(async (file) => {
        let uploadContent = file.text;

        // we need to strip the base64 prefix if it exists
        if (file.text.startsWith("data:")) {
          uploadContent = file.text.replace(/^data:.+;base64,/, "");
        }

        // if the uploadedFileName is empty, set it to file.filename
        if (uploadedFileName.value === "") {
          uploadedFileName.value = file.filename;
        }

        try {
          const response = await uploadArtifact(props.session, file.filename, uploadContent, file.mimetype)

          console.log("File uploaded successfully:", response);

          // parse the last text element from the response
          const lastText = extractADKText(response);

          const desc = JSON.parse(lastText);

          // add it to the list of artifacts
          artifacts.value.push({
            filename: `Figure ${desc.figure_number}`,
            title: desc.title,
            description: desc.description,
            mimetype: file.mimetype,
            text: file.text
          });
        }
        catch (error) {
          console.error("Error uploading file:", error);
        }
    }))
  }
  finally {
    isProcessing.value = false;
    uploadedFileName.value = "";
  }
}
</script>
