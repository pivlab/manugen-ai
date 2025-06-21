<template>
  <div class="app-preview">
    <div class="preview-content" v-html="renderedContent"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from "vue";
import showdown from "showdown";

const renderedContent = ref<string>("");

// props are the markdown content from the editor
type PropTypes = {
  content: string
};

const props = defineProps<PropTypes>();

// when content changes, render the markdown as HTML using showdown

const converter = new showdown.Converter();

watchEffect(() => {
  renderedContent.value = converter.makeHtml(props.content);
});

</script>
