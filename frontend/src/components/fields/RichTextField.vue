<template>
  <textarea 
    :id="fieldId" 
    class="pure-input-1" 
    rows="5" 
    :value="modelValue ?? ''" 
    @input="handleInput"
    :placeholder="field.placeholder"
  ></textarea>
</template>

<script setup>
const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldId = `field-${props.field.name}`

function handleInput(event) {
  emit('update:modelValue', event.target.value)
}
</script> 