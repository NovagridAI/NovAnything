<template>
  <div class="chat-header-menu">
    <div class="chat-title-container">
      <div class="chat-title">{{ currentChatTitle }}</div>
      <div class="menu-container">
        <arco-select v-model="selectedOption" @change="handleSelect" :allow-clear="false" :allow-search="false">
          <template #arrow-icon>
            <!-- 空元素替代箭头 -->
          </template>
          <arco-option v-for="(option) in chatSettingConfigured" :key="option.modelName" :value="option.modelName">
            {{ option.modelName }}
          </arco-option>
        </arco-select>
      </div>

    </div>
    <div class="icon-actions">
      <icon-list class="icon-list" @click="openFullscreenView" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { IconList } from '@arco-design/web-vue/es/icon';
import { ref } from 'vue';
import routeController from '@/controller/router';
import { useChatSetting } from '@/store/useChatSetting';
import { storeToRefs } from 'pinia';
import { useHomeChat } from '@/store/useHomeChat';
import urlResquest from '@/services/urlConfig';
const { chatId, historyList } = storeToRefs(useHomeChat());

const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { setAllChatSettingConfigured } = useChatSetting();


const defaultOption = chatSettingConfigured.value.find(item => item.active === true);
const { changePage } = routeController();
const selectedOption = computed(() => {
  return chatSettingConfigured.value.find(item => item.active === true)?.modelName || '无模型配置';
});
const currentChatTitle = computed(() => {
  const currentChatTitle = historyList.value.find(item => item.historyId === chatId.value);
  return currentChatTitle?.title || '新对话';
});

const isFullscreenViewOpen = ref(false);
const modelList = ref([]);

function handleSelect(option: string) {
  // 不需要手动设置selectedOption.value，因为v-model会自动处理
  // 这里可以添加其他处理逻辑
}

// 打开全屏视图
function openFullscreenView() {
  isFullscreenViewOpen.value = true;
  // 使用路由控制器跳转到全屏视图路由
  changePage('/fullscreen-view/knowledge');
}

// 获取模型列表
const fetchModelList = async () => {
  try {
    const response = await urlResquest.getModelList({}, {});
    if (response && response.data) {
      modelList.value = response.data.configs;
      console.log('获取到的模型列表:', modelList.value);

      // 将API返回的模型数据映射到chatSettingConfigured格式
      updateChatSettingWithModelList(modelList.value);
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models) => {
  if (!models || models.length === 0) return;


  // 将API返回的模型映射为chatSettingConfigured格式
  const customModels = models.map(model => {
    return {
      modelType: model.model_endpoint,
      modelName: model.service_name,
      customId: model.config_id,
      apiKey: model.api_key,
      apiBase: model.api_proxy,
      chunkSize: model.chunk_size || 800,
      apiModelName: model.service_name,
      apiContextLength: model.api_context_length || 4096,
      maxToken: Math.floor((model.max_token || 4096)),
      temperature: model.temperature || 0.5,
      top_P: model.top_P || 1.0,
      top_K: model.top_k || 40,
      context: model.context_length || 10,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      },
      active: false,
      // 保存原始数据，以便后续可能需要
      originalData: { ...model }
    };
  });
  console.log(customModels, 'customModels')
  // 更新chatSettingConfigured，使用新的批量设置函数
  setAllChatSettingConfigured([...customModels]);
};


onMounted(() => {
  fetchModelList();
})

</script>

<style scoped>
.chat-header-menu {
  height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #D8D8D8;
  background-color: #F8F8F8;
}

.chat-title-container {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .chat-title {
    margin-right: 16px;
    font-size: 16px;
    font-weight: 500;
    color: #1a1a1a;
  }
}

.icon-list {
  font-size: 16px;
  color: #4E5969;
  cursor: pointer;
  transition: all 0.3s;
}

.icon-list:hover {
  color: #5a47e5;
  transform: scale(1.1);
}

.icon-actions {
  display: flex;
  align-items: center;
}

:deep(.arco-select-view-suffix) {
  padding: 0px 0px;
}

/* 覆写 arco-select 样式 */
:deep(.arco-select-view-single) {

  background-color: #E8F7FF;
  color: #3491FA;
  padding: 4px 12px;
  font-weight: 500;
  padding: 0px 8px;
  border-color: #E8F7FF;
}

:deep(.arco-select-view-single:hover) {
  background-color: #D0EBFF !important;
  border-color: #3491FA !important;
}

:deep(.arco-select-view-value) {
  color: #3491FA;
  font-weight: 500;
  font-size: 14px;
  line-height: 24px;
}

:deep(.arco-select-arrow) {
  color: #3491FA;
  margin-top: -2px;
}

/* 确保下拉选项也使用相同的文字颜色 */
:deep(.arco-select-dropdown) {
  width: 100px;

  .arco-select-option {
    padding: 8px 12px;

    &.arco-select-option-active,
    &.arco-select-option-selected {
      color: #3491FA;
      background-color: #E8F7FF;
      border-radius: 4px;
    }

    &:hover {
      background-color: #E8F7FF;
    }
  }
}

/* 添加菜单容器样式 */
.menu-container {
  display: flex;
  align-items: center;
}
</style>
