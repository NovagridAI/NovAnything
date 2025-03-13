<template>
  <div class="department-container">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- <div class="header-actions">
        <a-button type="primary" @click="showCreateModal">创建部门</a-button>
      </div> -->

      <a-table :columns="columns" :data-source="dataSource" :pagination="false" :loading="tableLoading">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="enterDepartment(record)">{{ record.name }}</a>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 右侧边栏 -->
    <div class="right-sidebar">
      <div class="sidebar-header">
        <div class="department-name">{{ currentDepartment }}</div>
        <div class="department-desc">管理部门</div>
      </div>
      
      <div class="sidebar-content">
        <a-button type="primary" block @click="showCreateModal" :loading="createLoading">
          <plus-outlined />创建子部门
        </a-button>
        
        <a-divider />
        
        <a-menu mode="inline">
          <a-menu-item key="members" @click="showManageMembers">
            <team-outlined />
            <span>管理成员</span>
          </a-menu-item>
          <a-menu-item key="move" @click="showMoveModal">
            <swap-outlined />
            <span>移动部门</span>
          </a-menu-item>
          <a-menu-item key="delete" @click="showDeleteConfirm" :disabled="deleteLoading">
            <delete-outlined />
            <span>删除部门</span>
          </a-menu-item>
        </a-menu>
      </div>
    </div>

    <!-- 创建部门弹窗 -->
    <a-modal
      v-model:visible="createModalVisible"
      title="创建部门"
      @ok="handleCreateOk"
      @cancel="handleCreateCancel"
    >
      <a-form :model="createForm">
        <a-form-item label="名称">
          <a-input v-model:value="createForm.name" placeholder="部门名称" />
        </a-form-item>
        <a-form-item label="介绍">
          <a-textarea v-model:value="createForm.description" placeholder="介绍" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 管理成员弹窗 -->
    <a-modal
      v-model:visible="manageMembersVisible"
      title="管理成员"
      @ok="handleManageMembersOk"
      @cancel="handleManageMembersCancel"
    >
      <a-input-search
        v-model:value="searchMember"
        placeholder="搜索用户名"
        style="margin-bottom: 16px"
      />
      <a-table
        :columns="memberColumns"
        :data-source="memberList"
        :pagination="false"
        :row-selection="{ selectedRowKeys: selectedMembers, onChange: onSelectChange }"
      />
    </a-modal>

    <!-- 移动部门弹窗 -->
    <a-modal
      v-model:visible="moveModalVisible"
      title="移动部门"
      @ok="handleMoveOk"
      @cancel="handleMoveCancel"
    >
      <a-tree
        v-model:selectedKeys="selectedDepartments"
        :tree-data="departmentTree"
        @select="onDepartmentSelect"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  PlusOutlined, 
  TeamOutlined, 
  SwapOutlined, 
  DeleteOutlined 
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import urlResquest from '@/services/urlConfig'

const currentDepartment = ref('o5Ljw6jYZ7 Team')
const createModalVisible = ref(false)
const manageMembersVisible = ref(false)
const moveModalVisible = ref(false)
const searchMember = ref('')
const selectedMembers = ref([])
const selectedDepartments = ref([])

const dataSource = ref([])
const createForm = ref({
  name: '',
  description: ''
})

const columns = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
  }
]

const memberColumns = [
  {
    title: '用户名',
    dataIndex: 'username',
  }
]

const memberList = ref([
  {
    key: '1',
    username: 'Member',
  }
])

const departmentTree = ref([
  {
    title: 'o5Ljw6jYZ7 Team',
    key: '1',
    children: [
      {
        title: '222',
        key: '2',
      },
    ],
  }
])

// 添加 loading 状态
const tableLoading = ref(false)
const createLoading = ref(false)
const deleteLoading = ref(false)

// 获取部门列表
const getDepartmentList = async () => {
  tableLoading.value = true
  try {
    const res = await urlResquest.departmentList()
    if (res.code === 200) {
      dataSource.value = res.data.map(item => ({
        key: item.id,
        name: item.name
      }))
    } else {
      message.error(res.msg || '获取部门列表失败')
    }
  } catch (error) {
    console.error('获取部门列表失败:', error)
    message.error('获取部门列表失败')
  } finally {
    tableLoading.value = false
  }
}

// 创建部门
const handleCreateOk = async () => {
  createLoading.value = true
  try {
    const params: any = {
      name: createForm.value.name,
      description: createForm.value.description,
      user_id: localStorage.getItem('userId')
    }
    
    // if (currentDepartment.value !== 'o5Ljw6jYZ7 Team') {
    //   params.parent_id = currentDepartment.value
    // }

    const res = await urlResquest.createDepartment(params)
    if (res.code === 200) {
      message.success('创建部门成功')
      createModalVisible.value = false
      createForm.value = {
        name: '',
        description: ''
      }
      getDepartmentList()
    } else {
      message.error(res.msg || '创建部门失败')
    }
  } catch (error) {
    console.error('创建部门失败:', error)
    message.error('创建部门失败')
  } finally {
    createLoading.value = false
  }
}

const handleCreateCancel = () => {
  createModalVisible.value = false
  createForm.value = {
    name: '',
    description: ''
  }
}

const showCreateModal = () => {
  createModalVisible.value = true
}

const showManageMembers = () => {
  manageMembersVisible.value = true
}

const showMoveModal = () => {
  moveModalVisible.value = true
}

const showDeleteConfirm = () => {
  Modal.confirm({
    title: '删除警告',
    content: '确认删除该部门？',
    okText: '确认',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      deleteLoading.value = true
      try {
        // 处理删除逻辑
      } finally {
        deleteLoading.value = false
      }
    },
  })
}

const enterDepartment = (record) => {
  console.log('进入部门:', record)
}

onMounted(() => {
  getDepartmentList()
})
</script>

<style scoped>
.department-container {
  display: flex;
  height: 100%;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

.right-sidebar {
  width: 256px;
  border-left: 1px solid #f0f0f0;
  background: #fff;
}

.sidebar-header {
  padding: 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.department-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.department-desc {
  font-size: 14px;
  color: #666;
}

.sidebar-content {
  padding: 16px;
}

:deep(.ant-menu-inline) {
  border-right: none;
}

:deep(.ant-menu-item) {
  height: 40px;
  line-height: 40px;
  margin-top: 4px;
  margin-bottom: 4px;
}
</style>
