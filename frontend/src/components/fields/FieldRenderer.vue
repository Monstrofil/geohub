<template>
  <component 
    :is="fieldComponent" 
    :field="field" 
    :model-value="modelValue" 
    @update:model-value="handleUpdate"
  />
</template>

<script setup>
import { computed } from 'vue'
import TextField from './TextField.vue'
import NumberField from './NumberField.vue'
import BoolField from './BoolField.vue'
import EnumField from './EnumField.vue'
import RichTextField from './RichTextField.vue'

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: [String, Number, Boolean],
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fieldComponent = computed(() => {
  switch (props.field.type) {
    case 'str':
      return TextField
    case 'number':
      return NumberField
    case 'bool':
      return BoolField
    case 'enum':
      return EnumField
    case 'richtext':
      return RichTextField
    default:
      return TextField // fallback to text field
  }
})

function handleUpdate(value) {
  emit('update:modelValue', value)
}
</script> 