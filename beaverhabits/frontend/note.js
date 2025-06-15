// vuejs guide: https://vuejs.org/guide/introduction.html
export default {
  template: `
    <q-editor
      ref="qRef"
      v-bind="$attrs"
      v-model="inputValue"
    >
      <template v-for="(_, slot) in $slots" v-slot:[slot]="slotProps">
        <slot :name="slot" v-bind="slotProps || {}" />
      </template>
    </q-editor>
  `,

  props: {
    value: String,
  },
  data() {
    return {
      inputValue: this.value,
      emitting: true,
    };
  },
  // inputValue(v-model) <-> value(prop)
  watch: {
    value(newValue) {
      console.log("value changed", newValue);
      this.emitting = false;
      this.inputValue = newValue;
      this.$nextTick(() => (this.emitting = true));
    },
    inputValue(newValue) {
      console.log("inputValue changed", newValue, this.emitting);
      if (!this.emitting) return;
      this.$emit("update:value", newValue);
    },
  },
  methods: {
    updateValue() {
      console.log("updateValue called", this.inputValue);
      this.inputValue = this.value;
    },
    update_value() {
      console.log("update_value called", this.inputValue);
      this.inputValue = this.value;
    },
    send_value() {
      console.log("send_value called", this.inputValue);
      return {
        value: this.inputValue,
      };
    },
  },
};
