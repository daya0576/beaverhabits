// vuejs guide: https://vuejs.org/guide/introduction.html
export default {
  template: `
    <q-editor
      ref="qRef"
      @paste="onPaste"
      v-bind="$attrs"
      v-model="inputValue"

      :definitions="{
        save: {
          tip: 'Save your work',
          icon: 'save',
          handler: saveWork
        },
        upload: {
          tip: 'Upload to cloud',
          icon: 'cloud_upload',
          handler: uploadIt
        }
      }"
      :toolbar="[
        ['bold', 'italic', 'strike', 'underline'],
        ['undo', 'redo'],
        // ['upload', 'save']
      ]"
    >
      <template v-for="(_, slot) in $slots" v-slot:[slot]="slotProps">
        <slot :name="slot" v-bind="slotProps || {}" />
      </template>
    </q-editor>
  `,

  props: {
    value: String,
  },

  // inputValue(v-model) <-> value(prop)
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

  methods: {
    updateValue() {
      this.inputValue = this.value;
    },
    onPaste(evt) {
      // Let inputs do their thing, so we don't break pasting of links.
      if (evt.target.nodeName === "INPUT") return;
      let text, onPasteStripFormattingIEPaste;
      evt.preventDefault();
      evt.stopPropagation();
      if (evt.originalEvent && evt.originalEvent.clipboardData.getData) {
        text = evt.originalEvent.clipboardData.getData("text/plain");
        this.$refs.qRef.runCmd("insertText", text);
      } else if (evt.clipboardData && evt.clipboardData.getData) {
        text = evt.clipboardData.getData("text/plain");
        this.$refs.qRef.runCmd("insertText", text);
      } else if (window.clipboardData && window.clipboardData.getData) {
        if (!onPasteStripFormattingIEPaste) {
          onPasteStripFormattingIEPaste = true;
          this.$refs.qRef.runCmd("ms-pasteTextOnly", text);
        }
        onPasteStripFormattingIEPaste = false;
      }
    },
    saveWork () {
      
    },
    uploadIt () {
      // upload image
      this.$refs.qRef.uploadImage({
        url: "/api/upload",
        headers: {
          Authorization: "Bearer " + localStorage.getItem("token"),
        },
        onSuccess: (response) => {
          // handle success
          console.log("Upload successful:", response);
        },
        onError: (error) => {
          // handle error
          console.error("Upload failed:", error);
        },
      });
      
    },
  },
};
