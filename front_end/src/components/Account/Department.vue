<template>
  <div class="department-container">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- <div class="header-actions">
        <a-button type="primary" @click="showCreateModal">创建部门</a-button>
      </div> -->

      <a-table :columns="columns" :data-source="dataSource" :pagination="false">
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
        <a-button type="primary" block @click="showCreateModal">
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
          <a-menu-item key="delete" @click="showDeleteConfirm">
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
        <a-form-item label="头像 & 名称">
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

<script>
import { defineComponent, ref } from 'vue'
import { 
  PlusOutlined, 
  TeamOutlined, 
  SwapOutlined, 
  DeleteOutlined 
} from '@ant-design/icons-vue'
import { Modal } from 'ant-design-vue'

export default defineComponent({
  components: {
    PlusOutlined,
    TeamOutlined,
    SwapOutlined,
    DeleteOutlined
  },
  setup() {
    const currentDepartment = ref('o5Ljw6jYZ7 Team')
    const columns = [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
      },
    ]

    const dataSource = ref([
      {
        key: '1',
        name: 'o5Ljw6jYZ7 Team',
      },
      {
        key: '2',
        name: '222',
      },
    ])

    // 创建部门相关
    const createModalVisible = ref(false)
    const createForm = ref({
      name: '',
      description: '',
    })

    // 管理成员相关
    const manageMembersVisible = ref(false)
    const searchMember = ref('')
    const selectedMembers = ref([])
    const memberColumns = [
      {
        title: '用户名',
        dataIndex: 'username',
      },
    ]
    const memberList = ref([
      {
        key: '1',
        username: 'Member',
      },
    ])

    // 移动部门相关
    const moveModalVisible = ref(false)
    const selectedDepartments = ref([])
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
      },
    ])

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
      // 使用 ant design vue 的确认对话框
      Modal.confirm({
        title: '删除警告',
        content: '确认删除该部门？',
        okText: '确认',
        cancelText: '取消',
        okType: 'danger',
        onOk() {
          // 处理删除逻辑
        },
      })
    }

    const enterDepartment = (record) => {
      // 处理进入部门逻辑
      console.log('进入部门:', record)
    }

    return {
      currentDepartment,
      columns,
      dataSource,
      createModalVisible,
      createForm,
      manageMembersVisible,
      searchMember,
      selectedMembers,
      memberColumns,
      memberList,
      moveModalVisible,
      selectedDepartments,
      departmentTree,
      showCreateModal,
      showManageMembers,
      showMoveModal,
      showDeleteConfirm,
      enterDepartment,
    }
  },
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
