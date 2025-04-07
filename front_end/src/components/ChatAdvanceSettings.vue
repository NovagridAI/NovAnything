<template>
  <arco-popover position="top" trigger="hover">
    <template #content>
      <div class="settings-popover">
        <h3>高级设置</h3>

        <arco-form layout="horizontal" :label-col-props="{ span: 11 }" :wrapper-col-props="{ span: 13 }"
          :label-align="'left'">
          <arco-form-item field="apiContextLength" label="总Token数量：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="LLM输入和输出的总token数量上限">
                  <icon-question-circle />
                </arco-tooltip>
                <span>总Token数量：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider 
                :model-value="advanceSettingsStore.apiContextLength / 1024" 
                @update:model-value="value => advanceSettingsStore.apiContextLength = value * 1024"
                :min="modelType === 'ollama' ? 2 : 4"
                :max="openAIModelMax || 200" 
                :step="1" 
              />
              <arco-input-number 
                :model-value="advanceSettingsStore.apiContextLength / 1024"
                @update:model-value="value => advanceSettingsStore.apiContextLength = value * 1024"
                :min="modelType === 'ollama' ? 2 : 4"
                :max="openAIModelMax || 200" 
                :step="1" 
                :precision="0" 
                :hide-button="true"
              >
                <template #append>K</template>
              </arco-input-number>
            </div>
          </arco-form-item>

          <arco-form-item field="maxToken" label="输出Token数量：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="LLM输出的token数量上限，最大值为: 总Token数量 / 4">
                  <icon-question-circle />
                </arco-tooltip>
                <span>输出Token数量：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="advanceSettingsStore.maxToken" :min="1"
                :max="advanceSettingsStore.apiContextLength / TOKENRATIO" :step="1" />
              <arco-input-number v-model="advanceSettingsStore.maxToken" :min="1"
                :max="advanceSettingsStore.apiContextLength / TOKENRATIO" :step="1" :precision="0"
                :hide-button="true" />
            </div>
          </arco-form-item>

          <arco-form-item field="temperature" label="随机性：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="控制输出的随机性，较低值使输出更确定，较高值增加创意性">
                  <icon-question-circle />
                </arco-tooltip>
                <span>随机性：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="advanceSettingsStore.temperature" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="advanceSettingsStore.temperature" :min="0" :max="1" :step="0.01"
                :precision="2" :hide-button="true" />
            </div>
          </arco-form-item>

          <arco-form-item field="top_P" label="累积概率阈值：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="限制词汇选择范围，较低值使输出更聚焦，较高值增加多样性">
                  <icon-question-circle />
                </arco-tooltip>
                <span>累积概率阈值：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="advanceSettingsStore.top_P" :min="0" :max="1" :step="0.01" />
              <arco-input-number v-model="advanceSettingsStore.top_P" :min="0" :max="1" :step="0.01" :precision="2"
                :hide-button="true" />
            </div>
          </arco-form-item>

          <arco-form-item field="top_K" label="检索结果数量上限：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="检索算法取所有文档分片里最相关的分片数量上限">
                  <icon-question-circle />
                </arco-tooltip>
                <span>检索结果上限：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="advanceSettingsStore.top_K" :min="1" :max="100" :step="1" />
              <arco-input-number v-model="advanceSettingsStore.top_K" :min="1" :max="100" :step="1" :precision="0"
                :hide-button="true" />
            </div>
          </arco-form-item>

          <arco-form-item field="context" label="上下文消息数量：">
            <template #label>
              <div class="label-with-tooltip">
                <arco-tooltip content="单轮对话中保留的历史消息数量上限">
                  <icon-question-circle />
                </arco-tooltip>
                <span>上下文消息数量：</span>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="advanceSettingsStore.context" :min="0" :max="11" :step="1"
                :format-tooltip="sliderFormatter" />
            </div>
          </arco-form-item>
        </arco-form>
      </div>
    </template>
    <icon-settings class="action-icon" />
  </arco-popover>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { IconQuestionCircle, IconSettings } from '@arco-design/web-vue/es/icon';
import { useAdvanceSettings } from '@/store/useAdvanceSettings';
import { useChatSetting } from '@/store/useChatSetting';

const TOKENRATIO = 4;
const modelType = ref('openAI');
const openAIModelMax = ref(200);

// 获取状态管理
const advanceSettingsStore = useAdvanceSettings();
const { updateSettings } = advanceSettingsStore;
const { chatSettingConfigured } = storeToRefs(useChatSetting());

// 上下文条数格式化
const sliderFormatter = (value) => {
  return value >= 11 ? '无限制' : value;
};

watch(chatSettingConfigured, (newVal) => {
  const activeModel = newVal.find(item => item.active === true);
  if (advanceSettingsStore.modelType !== activeModel.modelType) {
    advanceSettingsStore.updateSettings({
      modelType: activeModel.modelType,
      apiContextLength: activeModel.apiContextLength,
      maxToken: activeModel.maxToken / TOKENRATIO,
      temperature: activeModel.temperature,
      top_P: activeModel.top_P,
      top_K: activeModel.top_K,
      context: activeModel.context,
    });
  }
});

defineOptions({
  name: 'ChatAdvanceSettings'
})
</script>

<style lang="scss" scoped>
.action-icon {
  font-size: 20px;
  color: #666666;
  cursor: pointer;

  &:hover {
    color: #4D71FF;
  }
}

.settings-popover {
  width: 380px;
  h3 {
    margin-top: 0;
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 500;
  }

  :deep(.arco-form-item) {
    margin-bottom: 16px;
  }

  :deep(.arco-form-item-label) {
    min-width: 120px;
    white-space: nowrap;
  }

  .label-with-tooltip {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;

    :deep(.arco-icon), .question-icon {
      font-size: 16px !important;
      color: #86909c;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      line-height: 1;

      &:hover {
        color: #165dff;
      }
    }
  }

  .param-control {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;

    :deep(.arco-slider) {
      flex: 1;
      max-width: 100px;
    }

    :deep(.arco-input-number) {
      width: 80px;
      flex-shrink: 0;
    }
  }
}
</style>