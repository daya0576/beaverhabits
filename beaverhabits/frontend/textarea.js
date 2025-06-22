export default {
  template: `
    <q-input
      ref="qRef"
      v-bind="$attrs"
      v-model="inputValue"
      :shadow-text="shadowText"
      @keydown.tab="perform_autocomplete"
      @paste="handlePaste"
      :list="id + '-datalist'"
      :for="id"
    >
      <template v-for="(_, slot) in $slots" v-slot:[slot]="slotProps">
        <slot :name="slot" v-bind="slotProps || {}" />
      </template>
    </q-input>
    <datalist v-if="withDatalist" :id="id + '-datalist'">
      <option v-for="option in this._autocomplete" :value="option"></option>
    </datalist>
  `,
  props: {
    id: String,
    _autocomplete: Array,
    value: String,
  },
  data() {
    return {
      inputValue: this.value,
      emitting: true,
    };
  },
  watch: {
    value(newValue) {
      this.emitting = false;
      this.inputValue = newValue;
      this.$nextTick(() => (this.emitting = true));
    },
    inputValue(newValue) {
      if (!this.emitting) return;
      this.$emit("update:value", newValue);
    },
  },
  computed: {
    shadowText() {
      if (!this.inputValue) return "";
      const matchingOption = this._autocomplete.find((option) =>
        option.toLowerCase().startsWith(this.inputValue.toLowerCase()),
      );
      return matchingOption ? matchingOption.slice(this.inputValue.length) : "";
    },
    withDatalist() {
      const isMobile =
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          navigator.userAgent,
        );
      return isMobile && this._autocomplete && this._autocomplete.length > 0;
    },
  },
  methods: {
    updateValue() {
      this.inputValue = this.value;
    },
    perform_autocomplete(e) {
      if (this.shadowText) {
        this.inputValue += this.shadowText;
        e.preventDefault();
      }
    },
    async handlePaste(event) {
      // Check if the paste event has clipboard data
      const items = event.clipboardData.items;
      const images = Array.from(items).filter((item) =>
        item.type.startsWith("image/"),
      );
      if (images.length === 0) {
        return;
      }

      // Prevent default paste behavior
      event.preventDefault();

      const placeholder = "<span>Loading...</span>";
      document.execCommand("insertHTML", false, placeholder);

      if (images.length > 0) {
        const imageFile = images[0].getAsFile();
        if (imageFile) {
          const url = await this.uploadImage(imageFile);
          if (url) {
            this.content = this.content.replace(
              placeholder,
              `<img src="${url}"/>`,
            );
          }
        }
      }
    },
    async uploadImage(imageFile) {
      const formData = new FormData();
      formData.append("file", imageFile);
      try {
        const response = await axios.post("/api/note/image", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        return response.data.url;
      } catch (error) {
        console.error("Image upload failed:", error);
        this.content = this.content.replace("Loading...", "Upload failed");
      }
    },
  },
};
