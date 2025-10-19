<template>
  <component 
    :is="fieldComponent" 
    :field="field" 
    :model-value="modelValue" 
    :disabled="disabled"
    @update:model-value="handleUpdate"
    @update:related-fields="handleRelatedFields"
  />
</template>

<script setup>
import { computed } from 'vue'
import TextField from './TextField.vue'
import NumberField from './NumberField.vue'
import BoolField from './BoolField.vue'
import EnumField from './EnumField.vue'
import RichTextField from './RichTextField.vue'
import KoatothChoiceField from './KoatothChoiceField.vue'

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: [String, Number, Boolean],
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:relatedFields'])

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
    case 'koatoth':
      return KoatothChoiceField
    default:
      return TextField // fallback to text field
  }
})

function handleUpdate(value) {
  emit('update:modelValue', value)
}

function handleRelatedFields(relatedData) {
  emit('update:relatedFields', {
    fieldName: props.field.name,
    relatedData: relatedData
  })
}
</script> 