import { createApp } from "vue";
import VueTippy from "vue-tippy";
import App from "@/App.vue";
import router from "@/router";
import "tippy.js/dist/tippy.css";
import "./styles.css";
import Vue3Toastify, { type ToastContainerOptions } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

const app = createApp(App);
app.use(router);

app.use(VueTippy, {
  directive: "tooltip",
  component: "AppTooltip",
  defaultProps: {
    appendTo: () => document.body,
    delay: [100, 0],
    duration: [300, 0],
    allowHTML: true,
    // onHide: () => false,
  },
});

app.use(
  Vue3Toastify,
  {
    autoClose: 1000,
    hideProgressBar: true,
    position: "bottom-left",
    type: "default",
    theme: "colored",
    transition: "slide",
    "dangerouslyHTMLString": true
  } as ToastContainerOptions,
);

app.mount("#app");
