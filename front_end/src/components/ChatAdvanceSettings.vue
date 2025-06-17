<template>
  <arco-popover position="top" trigger="click">
    <template #content>
      <div class="settings-popover">
        <h3>高级设置</h3>
        <div class="settings-note">
          <span>当前显示活跃模型配置，此处调整仅影响本次对话</span>
        </div>

        <arco-form
          layout="horizontal"
          :label-col-props="{ span: 10 }"
          :wrapper-col-props="{ span: 14 }"
          :label-align="'left'"
        >
          <arco-form-item field="apiContextLength" label="总Token数量：">
            <template #label>
              <div class="label-with-tooltip">
                <span>总Token数量</span>
                <arco-tooltip content="LLM输入和输出的总token数量上限">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider
                :model-value="userSettings.apiContextLength / 1024"
                :min="modelType === 'ollama' ? 2 : 4"
                :max="openAIModelMax || 10000"
                :step="1"
                @update:model-value="value => (userSettings.apiContextLength = value * 1024)"
              />
              <arco-input-number
                :model-value="userSettings.apiContextLength / 1024"
                :min="modelType === 'ollama' ? 2 : 4"
                :max="openAIModelMax || 10000"
                :step="1"
                :precision="0"
                :hide-button="true"
                @update:model-value="value => (userSettings.apiContextLength = value * 1024)"
              >
                <template #append>K</template>
              </arco-input-number>
            </div>
          </arco-form-item>

          <arco-form-item field="maxToken" label="输出Token数量：">
            <template #label>
              <div class="label-with-tooltip">
                <span>输出Token数量</span>
                <arco-tooltip content="LLM输出的token数量上限，最大值为: 总Token数量 / 4">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider
                v-model="userSettings.maxToken"
                :min="1"
                :max="userSettings.apiContextLength / TOKENRATIO"
                :step="1"
              />
              <arco-input-number
                v-model="userSettings.maxToken"
                :min="1"
                :max="userSettings.apiContextLength / TOKENRATIO"
                :step="1"
                :precision="0"
                :hide-button="true"
              />
            </div>
          </arco-form-item>

          <arco-form-item field="temperature" label="随机性：">
            <template #label>
              <div class="label-with-tooltip">
                <span>随机性</span>
                <arco-tooltip content="控制输出的随机性，较低值使输出更确定，较高值增加创意性">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="userSettings.temperature" :min="0" :max="1" :step="0.01" />
              <arco-input-number
                v-model="userSettings.temperature"
                :min="0"
                :max="1"
                :step="0.01"
                :precision="2"
                :hide-button="true"
              />
            </div>
          </arco-form-item>

          <arco-form-item field="top_P" label="累积概率阈值：">
            <template #label>
              <div class="label-with-tooltip">
                <span>累积概率阈值</span>
                <arco-tooltip content="限制词汇选择范围，较低值使输出更聚焦，较高值增加多样性">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="userSettings.top_P" :min="0" :max="1" :step="0.01" />
              <arco-input-number
                v-model="userSettings.top_P"
                :min="0"
                :max="1"
                :step="0.01"
                :precision="2"
                :hide-button="true"
              />
            </div>
          </arco-form-item>

          <arco-form-item field="top_K" label="检索结果数量上限：">
            <template #label>
              <div class="label-with-tooltip">
                <span>检索结果上限</span>
                <arco-tooltip content="检索算法取所有文档分片里最相关的分片数量上限">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider v-model="userSettings.top_K" :min="1" :max="100" :step="1" />
              <arco-input-number
                v-model="userSettings.top_K"
                :min="1"
                :max="100"
                :step="1"
                :precision="0"
                :hide-button="true"
              />
            </div>
          </arco-form-item>

          <arco-form-item field="context" label="上下文消息数量：">
            <template #label>
              <div class="label-with-tooltip">
                <span>上下文消息数量</span>
                <arco-tooltip content="单轮对话中保留的历史消息数量上限">
                  <icon-question-circle />
                </arco-tooltip>
              </div>
            </template>
            <div class="param-control">
              <arco-slider
                v-model="userSettings.context"
                :min="0"
                :max="11"
                :step="1"
                :format-tooltip="(val: number) => String(val >= 11 ? '无限制' : val)"
              />
            </div>
          </arco-form-item>
        </arco-form>
      </div>
    </template>
    <icon-settings
      v-if="userInfo?.role === 'admin' || userInfo?.role === 'superadmin'"
      class="action-icon"
    />
  </arco-popover>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { IconQuestionCircle, IconSettings } from '@arco-design/web-vue/es/icon';
import { useAdvanceSettings } from '@/store/useAdvanceSettings';
import { useChatSetting } from '@/store/useChatSetting';
import { useUser } from '@/store/useUser';

const TOKENRATIO = 4;
const modelType = ref('openAI');
const openAIModelMax = ref(10000);

// 获取状态管理
const { userSettings } = storeToRefs(useAdvanceSettings());
const { updateSettings } = useAdvanceSettings();
const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { userInfo } = storeToRefs(useUser());

// 上下文条数格式化
const sliderFormatter = (value: number): string => {
  return value >= 11 ? '无限制' : String(value);
};

// 监听活跃模型变化，同步到高级设置
watch(
  chatSettingConfigured,
  newVal => {
    const activeModel = newVal.find(item => item.active === true);
    console.log('activeModel', newVal);
    if (activeModel) {
      // 每次活跃模型变化时，都重新初始化高级设置
      updateSettings({
        modelType: activeModel.modelType,
        apiContextLength: activeModel.apiContextLength,
        maxToken: Math.min(activeModel.maxToken, activeModel.apiContextLength / TOKENRATIO),
        temperature: activeModel.temperature,
        top_P: activeModel.top_P,
        top_K: activeModel.top_K,
        context: activeModel.context,
      });
    }
  },
  {
    deep: true,
    immediate: true // 立即执行一次
  }
);

defineOptions({
  name: 'ChatAdvanceSettings',
});
</script>

<style lang="scss" scoped>
.action-icon {
  font-size: 20px;
  color: #666666;
  cursor: pointer;

  &:hover {
    color: #4d71ff;
  }
}

.settings-popover {
  width: 420px;

  h3 {
    margin-top: 0;
    margin-bottom: 8px;
    font-size: 16px;
    font-weight: 500;
  }

  .settings-note {
    margin-bottom: 16px;
    padding: 8px 12px;
    background-color: #f7f8fa;
    border-radius: 4px;
    border-left: 3px solid #165dff;
    
    span {
      font-size: 14px;
      color: #86909c;
    }
  }

  :deep(.arco-form-item) {
    margin-top: 0px;
    padding-bottom: 8px;
    padding-top: 8px;
    margin-bottom: 0px;
    border-bottom: 1px solid #d8d8d8;
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

    :deep(.arco-icon),
    .question-icon {
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
    gap: 8px;
    width: 100%;

    :deep(.arco-slider) {
      flex: 1;
      min-width: 120px;
    }

    :deep(.arco-input-number) {
      width: 100px;
      flex-shrink: 0;
    }
  }

  :deep(.arco-tooltip-content) {
    font-size: 14px;
    max-width: 250px;
    white-space: normal;
    line-height: 1.4;
  }
}
</style>
