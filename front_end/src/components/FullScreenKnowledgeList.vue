<script setup lang="ts">
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import OptionList from '@/components/OptionList.vue';
import { IconPlus } from '@arco-design/web-vue/es/icon';
import { storeToRefs } from 'pinia';
import { ref, computed, onMounted, watch } from 'vue';
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
  }
})

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
  return await resultControl(await urlResquest.createKb({ kb_name: newKbForm.value.kb_name, kb_type: kbType.value }));
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
</script>

<template>
  <arco-layout class="knowledge-layout">
    <arco-layout-sider class="knowledge-sidebar" width=312>
      <div class="knowledge-header">
        <h3>{{ headerTitle }}</h3>
        <p>{{ headerDesc }}</p>
      </div>

      <div class="knowledge-title">
        <span>{{ kbType === 'personal' ? '个人知识库' : '团队知识库' }}</span>
        <icon-plus class="add-icon" @click="openCreateModal" />
      </div>

      <arco-menu :selected-keys="[currentId]">
        <arco-menu-item v-for="(item) in filterKnowledgeBaseList" :key="item.kb_id" @click="manage(item)"
          style="margin: 12px 12px;">
          <template #icon>
            <img class="item-icon" :src="currentId === item?.kb_id ? menuActiveImg : menuDefaultImg" alt="文件夹"
              :class="{ 'icon-active': selectList.includes(item?.kb_id) }" />
          </template>
          {{ item.kb_name }}
        </arco-menu-item>
      </arco-menu>
    </arco-layout-sider>

    <arco-layout-content class="knowledge-content">
      <!-- 这里可以放置知识库内容 -->
      <OptionList />
    </arco-layout-content>
  </arco-layout>

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
  height: 100%;
}

.knowledge-sidebar {
  height: 100%;
  border-right: 1px solid var(--color-border);
  background-color: #fff;
}

.knowledge-header {
  padding: 16px;
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
}

.knowledge-content {
  padding: 16px;
  background-color: var(--color-bg-2);
}

:deep(.arco-menu-light) {
  border-right: none;
}

:deep(.arco-menu-selected) {
  background-color: #E0EAFF;
}

:deep(.arco-layout-sider) {
  width: 312px !important;
  max-width: 312px !important;
  min-width: 312px !important;
}

.add-icon {
  font-size: 16px;
  color: var(--color-text-1);
  cursor: pointer;
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
</style>