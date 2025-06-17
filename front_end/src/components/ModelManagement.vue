<template>
  <div class="model-management">
    <div class="model-management-header">
      <div class="model-management-header-title">
        模型管理
        <arco-button type="primary" @click="addNewModel" class="add-model-btn">
          <template #icon><icon-plus /></template>
          添加新模型
        </arco-button>
      </div>
    </div>

    <!-- 分割线 -->
    <arco-divider class="header-divider" />

    <arco-card :bordered="false" class="model-list-card">
      <div class="model-list-container">
        <!-- 没有模型时的提示 -->
        <div v-if="!modelList.length && !loading" class="empty-state">
          <div class="empty-content">
            <p class="empty-text">您还没有设置模型，点击设置第一个模型</p>
            <arco-button type="primary" size="large" @click="addNewModel" class="add-first-model">
              <template #icon><icon-plus /></template>
            </arco-button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <arco-spin size="32" />
          <p>正在加载模型列表...</p>
        </div>

        <!-- 有模型时的列表 -->
        <div v-else-if="modelList.length" class="model-list">
          <div v-for="model in currentPageModels" :key="model.config_id" class="model-item">
            <div class="model-name clickable" @click="showModelDetail(model)">{{ model.service_name }}</div>
            <div class="model-actions">
              <arco-button 
                v-if="model.config_id !== activeModelId" 
                type="outline" 
                size="small" 
                @click="setActiveModel(model)"
                class="action-btn"
              >
                设为活跃
              </arco-button>
              <arco-button 
                v-else
                type="primary" 
                size="small" 
                disabled
                class="action-btn"
              >
                已设置为活跃模型
              </arco-button>
              <arco-button 
                type="outline" 
                size="small" 
                @click="editModel(model)"
                class="action-btn"
              >
                修改配置
              </arco-button>
              <arco-button 
                type="outline" 
                status="danger" 
                size="small" 
                @click="showDeleteConfirm(model)"
                class="action-btn"
              >
                删除配置
              </arco-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页器 - 固定在底部 -->
      <div class="pagination-wrapper">
        <arco-pagination 
          v-if="modelList.length > 0"
          :current="currentPage" 
          :total="modelList.length" 
          :page-size="pageSize"
          @change="handlePageChange"
          show-total
          show-jumper
          size="small"
          :show-more="false"
        />
      </div>
    </arco-card>

    <!-- 删除确认弹窗 -->
    <arco-modal
      v-model:visible="deleteModalVisible"
      title="确认删除"
      @ok="confirmDelete"
      @cancel="cancelDelete"
    >
      <div v-if="modelToDelete?.config_id === activeModelId" class="delete-warning">
        <arco-alert type="warning" show-icon>
          <template #icon>
            <icon-exclamation-circle />
          </template>
          <template #title>
            您正在删除当前活跃模型
          </template>
          删除后系统会自动选择其他模型作为活跃模型。如果没有其他模型，所有用户将无法进行对话，请确保您有其他可用的模型配置。
        </arco-alert>
      </div>
      <p style="margin-top: 16px;">确定要删除模型"{{ modelToDelete?.service_name }}"吗？此操作不可撤销。</p>
    </arco-modal>

    <!-- 模型详情弹窗 -->
    <arco-modal
      v-model:visible="detailModalVisible"
      title="模型详情"
      :width="800"
      @cancel="closeModelDetail"
      :footer="false"
    >
      <div v-if="selectedModel" class="model-detail">
        <arco-descriptions :data="modelDetailData" :column="1" bordered />
      </div>
    </arco-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Message } from '@arco-design/web-vue';
import { IconPlus, IconExclamationCircle } from '@arco-design/web-vue/es/icon';
import urlResquest from '@/services/urlConfig';
import { useChatSetting } from '@/store/useChatSetting';
import { storeToRefs } from 'pinia';

const router = useRouter();
const { chatSettingConfigured } = storeToRefs(useChatSetting());
const { setAllChatSettingConfigured } = useChatSetting();

// 模型列表
const modelList = ref([]);
const activeModelId = ref('');
const loading = ref(false);

// 分页相关
const currentPage = ref(1);
const pageSize = ref(10);
const totalPages = computed(() => Math.ceil(modelList.value.length / pageSize.value));

// 计算当前页的模型
const currentPageModels = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return modelList.value.slice(start, end);
});

// 删除相关
const deleteModalVisible = ref(false);
const modelToDelete = ref(null);

// 模型详情相关
const detailModalVisible = ref(false);
const selectedModel = ref(null);
const modelDetailData = computed(() => {
  if (!selectedModel.value) return [];
  
  const model = selectedModel.value;
  return [
    { label: '模型名称', value: model.service_name },
    { label: '模型提供方', value: getProviderText(model.service_id) },
    { label: 'API密钥', value: model.api_key || '未设置' },
    { label: 'API路径', value: model.api_proxy || '未设置' },
    { label: '总Token数量', value: `${(model.api_context_length / 1000).toFixed(0)}K` },
    { label: '输出Token数量', value: model.max_token },
    { label: '随机性', value: model.temperature },
    { label: '累积概率阈值', value: model.top_p },
    { label: '检索结果数量上限', value: model.top_k },
    { label: '上下文消息数量', value: model.context_length },
    { label: '创建时间', value: model.create_time ? new Date(model.create_time).toLocaleString() : '未知' },
    { label: '更新时间', value: model.update_time ? new Date(model.update_time).toLocaleString() : '未知' },
    { label: '是否活跃', value: model.is_active ? '是' : '否' },
    { label: '是否全局', value: model.is_global ? '是' : '否' }
  ];
});

// 获取提供方文本
const getProviderText = (serviceId) => {
  switch(serviceId) {
    case 'openAI': return 'OpenAI';
    case 'ollama': return 'Ollama';
    case 'custom': return '自定义';
    default: return serviceId || '未知';
  }
};

// 获取模型列表
const fetchModelList = async () => {
  try {
    loading.value = true;
    const response = await urlResquest.getModelList({}, {});
    if (response && response.data) {
      modelList.value = response.data.configs || [];
      
      // 找到当前活跃的模型
      const activeModel = modelList.value.find(model => model.is_active);
      if (activeModel) {
        activeModelId.value = activeModel.config_id;
      }

      // 将API返回的模型数据映射到chatSettingConfigured格式
      updateChatSettingWithModelList(modelList.value);
    } else {
      modelList.value = [];
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
    // 不显示错误消息，避免用户看到错误提示
    modelList.value = [];
  } finally {
    loading.value = false;
  }
};

// 将API返回的模型列表更新到chatSettingConfigured
const updateChatSettingWithModelList = (models) => {
  if (!models || models.length === 0) return;

  console.log('ModelManagement: 开始处理模型数据映射:', models);

  // 将API返回的模型映射为chatSettingConfigured格式
  const customModels = models.map(model => {
    console.log('ModelManagement: 处理单个模型:', model);
    
    const mappedModel = {
      modelType: model.model_endpoint || model.service_name || '',
      modelName: model.service_name || '未知模型',
      customId: model.config_id || '',
      apiKey: model.api_key || '',
      apiBase: model.api_proxy || '',
      chunkSize: model.chunk_size || 800,
      apiModelName: model.service_name || '未知模型',
      serviceId: model.service_id || '',
      apiContextLength: model.api_context_length || 4096,
      maxToken: Math.floor((model.max_token || 4096)),
      temperature: model.temperature || 0.5,
      top_P: model.top_p || 1.0, // 修复：使用小写的top_p
      top_K: model.top_k || 40,
      context: model.context_length || 10,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      },
      active: model.is_active === 1 || model.is_active === true, // 修复：正确检查活跃状态
      originalData: { ...model }
    };
    
    console.log('ModelManagement: 映射后的模型:', mappedModel);
    console.log('ModelManagement: 活跃状态检查 - model.is_active:', model.is_active, 'mapped.active:', mappedModel.active);
    
    return mappedModel;
  });
  
  console.log('ModelManagement: 所有映射后的模型:', customModels);
  
  // 确保至少有一个活跃模型
  const hasActiveModel = customModels.some(model => model.active);
  if (!hasActiveModel && customModels.length > 0) {
    console.log('ModelManagement: 没有活跃模型，设置第一个为活跃');
    customModels[0].active = true;
  }
  
  console.log('ModelManagement: 最终的模型配置:', customModels);
  setAllChatSettingConfigured([...customModels]);
};

// 显示模型详情
const showModelDetail = async (model) => {
  try {
    // 获取完整的模型详情
    const response = await urlResquest.getModelDetail({ config_id: model.config_id });
    if (response && response.data) {
      selectedModel.value = response.data;
      detailModalVisible.value = true;
    } else {
      // 如果获取详情失败，使用列表中的数据
      selectedModel.value = model;
      detailModalVisible.value = true;
    }
  } catch (error) {
    console.error('获取模型详情失败:', error);
    // 使用列表中的数据作为备选
    selectedModel.value = model;
    detailModalVisible.value = true;
  }
};

// 关闭模型详情弹窗
const closeModelDetail = () => {
  detailModalVisible.value = false;
  selectedModel.value = null;
};

// 添加新模型
const addNewModel = () => {
  router.push('/fullscreen-view/model-settings');
};

// 修改模型配置
const editModel = (model) => {
  router.push(`/fullscreen-view/model-settings?id=${model.config_id}`);
};

// 设为活跃模型
const setActiveModel = async (model) => {
  try {
    const response = await urlResquest.setActiveModel({ config_id: model.config_id });
    if (response && response.code === 200) {
      Message.success('已设为当前活跃模型');
      activeModelId.value = model.config_id;
      
      // 更新本地状态
      modelList.value.forEach(item => {
        item.is_active = item.config_id === model.config_id;
      });
      
      // 重新更新chatSettingConfigured
      updateChatSettingWithModelList(modelList.value);
    } else {
      Message.error(response?.msg || '设置活跃模型失败');
    }
  } catch (error) {
    console.error('设置活跃模型失败:', error);
    Message.error('设置活跃模型失败');
  }
};

// 显示删除确认弹窗
const showDeleteConfirm = (model) => {
  modelToDelete.value = model;
  deleteModalVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  try {
    const response = await urlResquest.deleteModel({ config_id: modelToDelete.value.config_id });
    if (response && response.code === 200) {
      Message.success('删除成功');
      deleteModalVisible.value = false;
      modelToDelete.value = null;
      
      // 重新获取模型列表
      await fetchModelList();
    } else {
      Message.error(response?.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除失败:', error);
    Message.error('删除失败');
  }
};

// 取消删除
const cancelDelete = () => {
  deleteModalVisible.value = false;
  modelToDelete.value = null;
};

// 分页变化处理
const handlePageChange = (page) => {
  currentPage.value = page;
};

onMounted(() => {
  fetchModelList();
});
</script>

<style scoped lang="scss">
.model-management {
  padding: 20px;
  margin: 0 20px;
}

.model-management-header {
  margin-bottom: 0;
  
  .model-management-header-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: #1a1a1a;
    margin-left: 16px;
    
    .add-model-btn {
      font-size: 14px;
      margin-right: 16px;
    }
  }
}

.header-divider {
  margin: 16px 0;
  border-color: #e5e6eb;
}

.model-list-card {
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.model-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 520px; /* 为10个模型项预留空间，每个模型项约52px */
}

.model-list {
  flex: 1;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 16px;
  
  p {
    color: #86909c;
    font-size: 14px;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  
  .empty-content {
    text-align: center;
    
    .empty-text {
      font-size: 16px;
      color: #86909c;
      margin-bottom: 20px;
    }
    
    .add-first-model {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      font-size: 24px;
    }
  }
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  min-height: 52px; /* 固定每个模型项的最小高度 */
  
  &:last-child {
    border-bottom: none;
  }
  
  .model-name {
    font-size: 16px;
    font-weight: 500;
    color: #1d2129;
    
    &.clickable {
      cursor: pointer;
      color: #165dff;
      transition: color 0.2s;
      
      &:hover {
        color: #0e42d2;
        text-decoration: underline;
      }
    }
  }
  
  .model-actions {
    display: flex;
    gap: 8px;
    
    .action-btn {
      min-width: 80px;
    }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  min-height: 60px; /* 固定分页器区域高度 */
  align-items: center;
}

.model-detail {
  :deep(.arco-descriptions-item-label) {
    font-weight: 500;
    color: #1d2129;
  }
  
  :deep(.arco-descriptions-item-value) {
    color: #4e5969;
  }
}

.delete-warning {
  margin-bottom: 16px;
  
  :deep(.arco-alert-title) {
    font-weight: 600;
  }
  
  :deep(.arco-alert-content) {
    margin-top: 8px;
    line-height: 1.5;
  }
}
</style> 