<template>
  <div class="chat-source">
    <PdfView
      v-if="sourceType === 'pdf' && sourceUrl"
      :source-url="sourceUrl"
      :style="{
        transform: `scale(${zoomLevel})`,
      }"
    />
    <DocxView
      v-if="(sourceType === 'docx' || sourceType === 'doc') && sourceUrl"
      :source-url="sourceUrl"
      :style="{
        transform: `scale(${zoomLevel})`,
      }"
    />
    <ExcelView
      v-if="(sourceType === 'xlsx' || sourceType === 'xls') && sourceUrl"
      :source-url="sourceUrl"
      :style="{
        transform: `scale(${zoomLevel})`,
      }"
    />
    <a-image
      v-if="imageArr.includes(sourceType) && sourceUrl"
      :src="sourceUrl"
      :preview-mask="false"
      :style="{
        transform: `scale(${zoomLevel})`,
      }"
    />
    <div
      v-if="
        sourceType === 'txt' ||
        sourceType === 'csv' ||
        sourceType === 'eml' ||
        sourceType === 'jsonl' ||
        sourceType === 'ppt' ||
        sourceType === 'pptx'
      "
      class="txt"
      :style="{ whiteSpace: 'pre-wrap', transform: `scale(${zoomLevel})` }"
    >
      {{ textContent }}
    </div>
    <HighLightMarkDown
      v-if="sourceType === 'md'"
      class="txt"
      :content="textContent"
      :style="{
        transform: `scale(${zoomLevel})`,
      }"
    />
  </div>
</template>

<script setup lang="ts">
import PdfView from '@/components/Source/PdfView.vue';
import ExcelView from '@/components/Source/ExcelView.vue';
import DocxView from '@/components/Source/DocxView.vue';
import HighLightMarkDown from '@/components/HighLightMarkDown.vue';
import { useChatSource } from '@/store/useChatSource';

const props = defineProps({
  zoomLevel: {
    type: Number,
    require: false,
    default: 1,
  },
});

const { zoomLevel } = toRefs(props);

const { sourceUrl, sourceType, textContent } = storeToRefs(useChatSource());
console.log(sourceType, sourceUrl);
let imageArr = ['jpg', 'png', 'jpeg'];
</script>

<style lang="scss" scoped>
.chat-source {
  width: 100%;
  min-height: 35vh;
  max-height: calc(90vh - 48px);
  //overflow-y: scroll;
  border-radius: 8px;
  display: flex;

  & * {
    transition: transform 0.3s ease;
    transform-origin: 0 0;
  }

  &::-webkit-scrollbar {
    height: 10px !important;
  }

  .txt {
    width: 100%;
    height: auto;
    padding: 15px 20px 30px 20px;
  }

  :deep(.ant-image) {
    margin: 5px auto;
    max-width: 100%;
  }
}
</style>
