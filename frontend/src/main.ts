import { createApp } from "vue";
import VueTippy from "vue-tippy";
import App from "./App.vue";
import router from "./router";
import "tippy.js/dist/tippy.css";
import "./styles.css";

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

app.mount("#app");
