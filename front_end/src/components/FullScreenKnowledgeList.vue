<script setup lang="ts">
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { useUser } from '@/store/useUser';
import OptionList from '@/components/OptionList.vue';
import { IconPlus, IconDelete } from '@arco-design/web-vue/es/icon';
import { storeToRefs } from 'pinia';
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Modal, Message, Input, Form, FormItem } from '@arco-design/web-vue';
import { resultControl } from '@/utils/utils';
import urlResquest from '@/services/urlConfig';
// 导入图片资源
import menuActiveImg from '../assets/home/menu-active.png';
import menuDefaultImg from '../assets/home/menu-default.png';

const { knowledgeBaseList = [], currentId }: any = storeToRefs(useKnowledgeBase());
const { setCurrentId, setCurrentKbName, getList } = useKnowledgeBase();
const { selectList } = storeToRefs(useKnowledgeBase());
const { userInfo } = storeToRefs(useUser());

const route = useRoute();

// 知识库类型（个人/组织）
const kbType = ref('personal');

// 根据路由路径确定知识库类型
const updateKbType = () => {
  // 从路径中获取类型
  const pathParts = route.path.split('/');
  const lastPart = pathParts[pathParts.length - 1];

  if (lastPart === 'organization') {
    kbType.value = 'team';
  } else {
    kbType.value = 'personal';
  }
};

// 监听路由变化
watch(() => route.path, () => {
  updateKbType();
}, { immediate: true });

// 计算标题
const headerTitle = computed(() => {
  return kbType.value === 'personal' ? '个人知识库管理' : '团队知识库管理';
});

// 计算描述
const headerDesc = computed(() => {
  return kbType.value === 'personal' ? '管理个人的知识库' : '管理团队的知识库';
});

const filterKnowledgeBaseList = computed(() => {
  return knowledgeBaseList.value.filter(item => item.kb_type === kbType.value)
})



const manage = item => {
  console.log(item)
  setCurrentId(item.kb_id);
  setCurrentKbName(item.kb_name);
};

watch(kbType, () => {
  console.log(kbType.value)
  if (filterKnowledgeBaseList.value.length > 0) {
    manage(filterKnowledgeBaseList.value[0])
  } else {
    // 当知识库列表为空时，清空当前选中的知识库
    setCurrentId('');
    setCurrentKbName('');
  }
})

// 监听过滤后的知识库列表变化，当列表为空时清空选中状态
watch(filterKnowledgeBaseList, (newList) => {
  console.log('filterKnowledgeBaseList 变化:', newList.length)
  if (newList.length === 0) {
    // 知识库列表为空时，清空当前选中的知识库
    setCurrentId('');
    setCurrentKbName('');
  } else if (!currentId.value || !newList.find(kb => kb.kb_id === currentId.value)) {
    // 如果当前没有选中的知识库，或者当前选中的知识库不在列表中，选择第一个
    manage(newList[0]);
  }
}, { immediate: true })

onMounted(() => {
  updateKbType();
});

// 新增知识库相关
const createModalVisible = ref(false);
const newKbForm = ref({
  kb_name: '',
  kb_desc: ''
});

// 打开创建知识库弹窗
const openCreateModal = () => {
  // 如果是团队知识库页面且用户是管理员，不允许创建
  if (kbType.value === 'team' && userInfo.value?.role === 'admin') {
    Message.error('只有超级管理员可以创建团队知识库');
    return;
  }
  
  createModalVisible.value = true;
  newKbForm.value = {
    kb_name: '',
    kb_desc: ''
  };
};

// 确认创建知识库
const confirmCreate = async () => {
  console.log(newKbForm.value)
  if (!newKbForm.value.kb_name.trim()) {
    Message.error('知识库名称不能为空');
    return;
  }

  // 这里添加创建知识库的逻辑
  console.log('创建知识库:', newKbForm.value);
  await addKb();
  // TODO: 调用API创建知识库

  createModalVisible.value = false;
  Message.success('知识库创建成功');
};

// 取消创建
const cancelCreate = () => {
  createModalVisible.value = false;
};

const createKb = async () => {
  const params = { 
    kb_name: newKbForm.value.kb_name, 
    kb_type: kbType.value 
  };
  
  // 只有在描述不为空时才传递description参数
  if (newKbForm.value.kb_desc && newKbForm.value.kb_desc.trim()) {
    params.description = newKbForm.value.kb_desc.trim();
  }
  
  return await resultControl(await urlResquest.createKb(params));
};


const addKb = async () => {
  try {
    const res: any = await createKb();
    // const res: any = await resultControl(await urlResquest.createKb({ kb_name: kb_name.value }));
    setCurrentId(res?.kb_id);
    setCurrentKbName(res?.kb_name);
    selectList.value.push(res?.kb_id);
    await getList();
  } catch (e) {
    console.log(e);
    Message.error(e.msg);
  }
};

// 删除知识库确认
const confirmDeleteKb = (item) => {
  Modal.confirm({
    title: '删除知识库',
    content: `确定要删除知识库 "${item.kb_name}" 吗？删除后无法恢复。`,
    okText: '确认删除',
    cancelText: '取消',
    okButtonProps: {
      status: 'danger'
    },
    onOk: () => {
      deleteKb(item.kb_id);
    }
  });
};

// 删除知识库
const deleteKb = async (kbId) => {
  try {
    await resultControl(await urlResquest.deleteKB({ kb_ids: [kbId] }));
    Message.success('知识库删除成功');
    
    // 重新获取知识库列表
    await getList();
    
    // 检查删除后的状态，如果当前类型的知识库列表为空，清空选择
    const updatedFilteredList = knowledgeBaseList.value.filter(item => item.kb_type === kbType.value);
    if (updatedFilteredList.length === 0) {
      setCurrentId('');
      setCurrentKbName('');
    } else if (currentId.value === kbId) {
      // 如果删除的是当前选中的知识库，选择第一个可用的知识库
      manage(updatedFilteredList[0]);
    }
  } catch (e) {
    console.log(e);
    Message.error(e?.msg || '删除知识库失败');
  }
};

// 存储事件处理函数的引用
let preventWheel;
let preventKeyboardScroll;
let knowledgeLayout;
let sidebar;
let content;

onBeforeUnmount(() => {
  // 移除之前的滚动锁定清理代码
});
</script>

<template>
  <div class="knowledge-layout">
    <div class="knowledge-sidebar">
      <div class="knowledge-header">
        <h3>{{ headerTitle }}</h3>
        <p>{{ headerDesc }}</p>
      </div>

      <div class="knowledge-title">
        <span>{{ kbType === 'personal' ? '个人知识库' : '团队知识库' }}</span>
        <icon-plus 
          v-if="!(kbType === 'team' && userInfo?.role === 'admin')"
          class="add-icon" 
          @click="openCreateModal" 
        />
      </div>

      <!-- 分隔线 -->
      <div class="separator"></div>

      <!-- 可滚动的知识库列表 -->
      <div class="knowledge-list-container">
        <arco-menu :selected-keys="[currentId]">
          <arco-tooltip 
            v-for="(item) in filterKnowledgeBaseList" 
            :key="item.kb_id"
            :content="item.description"
            :disabled="!item.description || !item.description.trim()"
            position="right"
            :trigger="'hover'"
            :auto-fit-popup-width="true"
            :popup-container="'body'"
          >
            <arco-menu-item @click="manage(item)" style="margin: 12px 12px; position: relative;">
              <template #icon>
                <img class="item-icon" :src="currentId === item?.kb_id ? menuActiveImg : menuDefaultImg" alt="文件夹"
                  :class="{ 'icon-active': selectList.includes(item?.kb_id) }" />
              </template>
              {{ item.kb_name }}
              <!-- 删除按钮：超级管理员在个人和团队知识库都可以删除，管理员只能删除个人知识库，普通用户只能删除个人知识库 -->
              <icon-delete v-if="(userInfo?.role === 'superadmin') || (kbType === 'personal' && (userInfo?.role === 'admin' || userInfo?.role === 'user'))"
                class="delete-icon" 
                style="font-size: 18px !important; width: 18px !important; height: 18px !important;"
                @click.stop="confirmDeleteKb(item)" 
                title="删除知识库" />
            </arco-menu-item>
          </arco-tooltip>
        </arco-menu>
      </div>
    </div>

    <div class="knowledge-content">
      <!-- 这里可以放置知识库内容 -->
      <OptionList class="knowledge-management" />
    </div>
  </div>

  <!-- 新建知识库弹窗 -->
  <Modal v-model:visible="createModalVisible" @cancel="cancelCreate" title="新建知识库" @ok="confirmCreate"
    :mask-closable="false">
    <div class="create-kb-form">
      <div class="form-item">
        <div class="form-label">知识库名称</div>
        <Input v-model="newKbForm.kb_name" placeholder="请输入知识库名称" />
      </div>

      <div class="form-item">
        <div class="form-label">知识库描述</div>
        <Input v-model="newKbForm.kb_desc" placeholder="请输入知识库描述" type="textarea" />
      </div>
    </div>
  </Modal>
</template>

<style scoped lang="scss">
.knowledge-layout {
  height: 100vh !important;
  max-height: 100vh !important;
  display: flex;
  flex-direction: row;
  overflow: hidden !important;
  position: relative;
}

.knowledge-sidebar {
  width: 312px;
  min-width: 312px;
  max-width: 312px;
  height: 100vh;
  border-right: 1px solid var(--color-border);
  background-color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.knowledge-header {
  padding: 16px;
  flex-shrink: 0;
}

.knowledge-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: #1a1a1a;
}

.knowledge-header p {
  margin: 4px 0 0;
  font-size: 16px;
  color: #767676;
}

.knowledge-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  font-weight: 500;
  color: var(--color-text-1);
  flex-shrink: 0;
}

.separator {
  height: 1px;
  background-color: var(--color-border);
  margin: 0 16px;
  flex-shrink: 0;
}

.knowledge-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  min-height: 0; /* 确保可以收缩 */
}

.knowledge-content {
  background-color: var(--color-bg-2);
  flex: 1;
  height: 100vh !important;
  max-height: 100vh !important;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  
  .knowledge-management {
    flex: 1;
    margin: 16px;
    background: #fff;
    border-radius: 8px;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 32px); /* 减去16px * 2 margin */
  }
}

:deep(.arco-menu-light) {
  border-right: none;
}

:deep(.arco-menu) {
  height: auto;
}

:deep(.arco-menu-selected) {
  background-color: #E0EAFF;
}



.add-icon {
  font-size: 16px;
  color: var(--color-text-1);
  cursor: pointer;
}

.item-icon {
  width: 20px;
  height: 20px;
  opacity: 0.6;
}

.icon-active {
  opacity: 1;
}

.delete-icon {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px !important;
  width: 18px !important;
  height: 18px !important;
  color: #999;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
  padding: 4px;
  z-index: 10;
  
  &:hover {
    color: #ff4757;
    opacity: 1 !important;
  }
}

:deep(.arco-menu-item) {
  position: relative;
  
  &:hover .delete-icon {
    opacity: 1;
  }
  
  .delete-icon {
    font-size: 18px !important;
    width: 18px !important;
    height: 18px !important;
  }
}

.create-kb-form {
  padding: 8px 0;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--color-text-1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}

:deep(.arco-menu-light .arco-menu-item.arco-menu-selected) {
  background-color: #E0EAFF !important;
}

:deep(.arco-menu-light .arco-menu-item:hover) {
  background-color: #E0EAFF !important;
}

/* 允许必要的弹窗组件正常显示 */
:deep(.arco-dropdown),
:deep(.arco-select-dropdown),
:deep(.arco-popover),
:deep(.arco-tooltip),
:deep(.arco-modal),
:deep(.arco-popconfirm) {
  overflow: visible !important;
}
</style>