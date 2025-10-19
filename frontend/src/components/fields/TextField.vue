<template>
  <div class="text-field">
    <input 
      :id="fieldId" 
      type="text" 
      class="pure-input-1" 
      :value="modelValue ?? ''" 
      @blur="handleBlur"
      :placeholder="field.placeholder"
      :disabled="disabled"
    />
    <div v-if="field.description" class="field-description">
      {{ field.description }}
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: [String, Number],
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`

function handleBlur(event) {
  if (props.disabled) return
  const newValue = event.target.value
  if (newValue !== (props.modelValue ?? '')) {
    emit('update:modelValue', newValue)
  }
}
</script>

<style scoped>
.field-description {
  font-size: 0.85em;
  color: #666;
  margin-top: 0.25rem;
  line-height: 1.3;
}
</style> 