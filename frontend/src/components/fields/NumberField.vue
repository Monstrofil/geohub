<template>
  <input 
    :id="fieldId" 
    type="number" 
    class="pure-input-1" 
    :value="modelValue ?? ''" 
    @input="handleInput"
    :placeholder="field.placeholder"
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
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`

function handleInput(event) {
  const value = event.target.value === '' ? null : Number(event.target.value)
  emit('update:modelValue', value)
}
</script> 