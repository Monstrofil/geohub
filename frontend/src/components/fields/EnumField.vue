<template>
  <select :id="fieldId" class="pure-input-1" :value="modelValue ?? ''" @change="handleChange">
    <option :value="''">—</option>
    <option v-for="option in field.values" :key="option" :value="option">{{ option }}</option>
  </select>
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

function handleChange(event) {
  const value = event.target.value === '' ? null : event.target.value
  emit('update:modelValue', value)
}
</script> 