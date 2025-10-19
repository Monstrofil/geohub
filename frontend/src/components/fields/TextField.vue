<template>
  <input 
    :id="fieldId" 
    type="text" 
    class="pure-input-1" 
    :value="modelValue ?? ''" 
    @blur="handleBlur"
    :placeholder="field.placeholder"
    :disabled="disabled"
  />
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