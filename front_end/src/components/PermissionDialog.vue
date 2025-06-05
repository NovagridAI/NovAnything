<template>
  <arco-modal
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    title="权限设置"
    :mask-closable="false"
    :footer="false"
    width="900px"
    @cancel="handleCancel"
  >
    <div class="permission-dialog">
      <div class="permission-tabs">
        <div class="tab-section">
          <div class="tab-header">
            <span>可添加用户</span>
            <span class="count">{{ availableCount }}/{{ totalAvailableCount }}</span>
          </div>
          <arco-input-search
            v-model="availableSearchText"
            placeholder="搜索"
            allow-clear
            @search="handleAvailableSearch"
          />
          <div class="user-list">
            <!-- 添加加载状态 -->
            <arco-spin :loading="loading" class="loading-container">
              <!-- 使用树形结构展示部门和用户 -->
              <arco-tree
                :data="availableTreeData"
                :default-expanded-keys="availableExpandedKeys"
                v-model:expanded-keys="availableExpandedKeys"
                :checkable="true"
                v-model:checked-keys="availableCheckedKeys"
                :check-strictly="true"
                @check="handleAvailableCheck"
              >
                <template #title="{ title }">
                  <span>{{ title }}</span>
                </template>
              </arco-tree>
            </arco-spin>
          </div>
        </div>

        <div class="tab-actions">
          <arco-button type="text" @click="addUsers">
            <template #icon><icon-right /></template>
          </arco-button>
          <arco-button type="text" @click="removeUsers">
            <template #icon><icon-left /></template>
          </arco-button>
        </div>

        <div class="tab-section">
          <div class="tab-header">
            <span>已添加用户</span>
            <span class="count">{{ assignedCount }}/{{ totalAssignedCount }}</span>
          </div>
          <arco-input-search
            v-model="assignedSearchText"
            placeholder="搜索"
            allow-clear
            @search="handleAssignedSearch"
          />
          <div class="user-list">
            <!-- 添加加载状态 -->
            <arco-spin :loading="loading" class="loading-container">
              <!-- 使用树形结构展示已分配的部门和用户 -->
              <arco-tree
                :data="assignedTreeData"
                :default-expanded-keys="assignedExpandedKeys"
                v-model:expanded-keys="assignedExpandedKeys"
                :checkable="true"
                v-model:checked-keys="assignedCheckedKeys"
                :check-strictly="true"
                @check="handleAssignedCheck"
              >
                <template #title="{ title }">
                  <span>{{ title }}</span>
                </template>
              </arco-tree>
            </arco-spin>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <arco-button @click="handleCancel">取消</arco-button>
        <arco-button type="primary" @click="handleConfirm" :loading="loading">确认</arco-button>
      </div>
    </div>
  </arco-modal>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { IconRight, IconLeft } from '@arco-design/web-vue/es/icon';
import urlRequest from '@/services/urlConfig';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  kbId: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:visible', 'confirm', 'cancel']);

// 数据状态
const loading = ref(false);
const kbData = ref(null);
const availableSearchText = ref('');
const assignedSearchText = ref('');
const assignedUserIds = ref([]);
const assignedDeptIds = ref([]);

// 树形控件状态
const availableCheckedKeys = ref([]);
const assignedCheckedKeys = ref([]);
const availableExpandedKeys = ref([]);
const assignedExpandedKeys = ref([]);

// 获取权限数据
const fetchPermissionData = async () => {
  loading.value = true;
  try {
    // 使用urlRequest调用API获取权限数据
    const result = await urlRequest.getKbPermissionData({ kb_id: props.kbId });

    if (result.code === 200) {
      kbData.value = result.data;
      
      // 初始化已分配用户和部门
      assignedUserIds.value = Object.keys(result.data.permissions.user);
      assignedDeptIds.value = Object.keys(result.data.permissions.department);
      
      // 初始化展开的节点
      initExpandedKeys();
    }
  } catch (error) {
    console.error('获取权限数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 初始化展开的节点
const initExpandedKeys = () => {
  if (!kbData.value) return;
  
  const deptKeys = [];
  
  // 添加所有部门ID作为默认展开的节点
  kbData.value.departments.forEach(dept => {
    deptKeys.push(dept.dept_id);
    
    dept.children.forEach(child => {
      deptKeys.push(child.dept_id);
      
      child.children.forEach(grandChild => {
        deptKeys.push(grandChild.dept_id);
      });
    });
  });
  
  availableExpandedKeys.value = [...deptKeys];
  assignedExpandedKeys.value = [...deptKeys];
};

// 构建可用树形数据
const availableTreeData = computed(() => {
  if (!kbData.value) return [];
  
  const searchText = availableSearchText.value.toLowerCase();
  
  // 构建树形数据
  return kbData.value.departments.map(dept => {
    // 部门节点
    const deptNode = {
      key: dept.dept_id,
      title: dept.dept_name,
      children: []
    };
    
    // 添加部门下的用户
    dept.users.forEach(user => {
      if (!assignedUserIds.value.includes(user.user_id) && 
          (!searchText || user.username.toLowerCase().includes(searchText))) {
        deptNode.children.push({
          key: user.user_id,
          title: user.username,
          isLeaf: true
        });
      }
    });
    
    // 添加子部门
    dept.children.forEach(child => {
      const childNode = {
        key: child.dept_id,
        title: child.dept_name,
        children: []
      };
      
      // 添加子部门下的用户
      child.users.forEach(user => {
        if (!assignedUserIds.value.includes(user.user_id) && 
            (!searchText || user.username.toLowerCase().includes(searchText))) {
          childNode.children.push({
            key: user.user_id,
            title: user.username,
            isLeaf: true
          });
        }
      });
      
      // 添加孙部门
      child.children.forEach(grandChild => {
        const grandChildNode = {
          key: grandChild.dept_id,
          title: grandChild.dept_name,
          children: []
        };
        
        // 添加孙部门下的用户
        grandChild.users.forEach(user => {
          if (!assignedUserIds.value.includes(user.user_id) && 
              (!searchText || user.username.toLowerCase().includes(searchText))) {
            grandChildNode.children.push({
              key: user.user_id,
              title: user.username,
              isLeaf: true
            });
          }
        });
        
        if (grandChildNode.children.length > 0 || assignedDeptIds.value.includes(grandChild.dept_id)) {
          childNode.children.push(grandChildNode);
        }
      });
      
      if (childNode.children.length > 0 || assignedDeptIds.value.includes(child.dept_id)) {
        deptNode.children.push(childNode);
      }
    });
    
    return deptNode;
  });
});

// 构建已分配树形数据
const assignedTreeData = computed(() => {
  if (!kbData.value) return [];
  
  const searchText = assignedSearchText.value.toLowerCase();
  
  // 构建树形数据
  return kbData.value.departments.map(dept => {
    // 部门节点
    const deptNode = {
      key: dept.dept_id,
      title: dept.dept_name,
      children: []
    };
    
    // 添加部门下的已分配用户
    dept.users.forEach(user => {
      if (assignedUserIds.value.includes(user.user_id) && 
          (!searchText || user.username.toLowerCase().includes(searchText))) {
        deptNode.children.push({
          key: user.user_id,
          title: user.username,
          isLeaf: true
        });
      }
    });
    
    // 添加子部门
    dept.children.forEach(child => {
      const childNode = {
        key: child.dept_id,
        title: child.dept_name,
        children: []
      };
      
      // 添加子部门下的已分配用户
      child.users.forEach(user => {
        if (assignedUserIds.value.includes(user.user_id) && 
            (!searchText || user.username.toLowerCase().includes(searchText))) {
          childNode.children.push({
            key: user.user_id,
            title: user.username,
            isLeaf: true
          });
        }
      });
      
      // 添加孙部门
      child.children.forEach(grandChild => {
        const grandChildNode = {
          key: grandChild.dept_id,
          title: grandChild.dept_name,
          children: []
        };
        
        // 添加孙部门下的已分配用户
        grandChild.users.forEach(user => {
          if (assignedUserIds.value.includes(user.user_id) && 
              (!searchText || user.username.toLowerCase().includes(searchText))) {
            grandChildNode.children.push({
              key: user.user_id,
              title: user.username,
              isLeaf: true
            });
          }
        });
        
        if (grandChildNode.children.length > 0 || assignedDeptIds.value.includes(grandChild.dept_id)) {
          childNode.children.push(grandChildNode);
        }
      });
      
      if (childNode.children.length > 0 || assignedDeptIds.value.includes(child.dept_id)) {
        deptNode.children.push(childNode);
      }
    });
    
    return deptNode;
  });
});

// 计算可用用户数量
const availableCount = computed(() => {
  return availableCheckedKeys.value.length;
});

// 计算总可用用户数量
const totalAvailableCount = computed(() => {
  if (!kbData.value) return 0;
  
  let count = 0;
  kbData.value.departments.forEach(dept => {
    dept.users.forEach(user => {
      if (!assignedUserIds.value.includes(user.user_id)) {
        count++;
      }
    });
    
    dept.children.forEach(child => {
      child.users.forEach(user => {
        if (!assignedUserIds.value.includes(user.user_id)) {
          count++;
        }
      });
      
      child.children.forEach(grandChild => {
        grandChild.users.forEach(user => {
          if (!assignedUserIds.value.includes(user.user_id)) {
            count++;
          }
        });
      });
    });
  });
  
  return count;
});

// 计算已分配用户数量
const assignedCount = computed(() => {
  return assignedCheckedKeys.value.length;
});

// 计算总已分配用户数量
const totalAssignedCount = computed(() => {
  return assignedUserIds.value.length + assignedDeptIds.value.length;
});

// 添加用户和部门
const addUsers = () => {
  if (availableCheckedKeys.value.length === 0) return;
  
  // 分离用户ID和部门ID
  const userKeys = [];
  const deptKeys = [];
  
  availableCheckedKeys.value.forEach(key => {
    if (key.startsWith('user_')) {
      userKeys.push(key);
    } else if (key.startsWith('dept_')) {
      deptKeys.push(key);
    }
  });
  
  // 添加用户
  userKeys.forEach(userId => {
    if (!assignedUserIds.value.includes(userId)) {
      assignedUserIds.value.push(userId);
    }
  });
  
  // 添加部门
  deptKeys.forEach(deptId => {
    if (!assignedDeptIds.value.includes(deptId)) {
      assignedDeptIds.value.push(deptId);
    }
  });
  
  // 清空选中
  availableCheckedKeys.value = [];
};

// 移除用户和部门
const removeUsers = () => {
  if (assignedCheckedKeys.value.length === 0) return;
  
  // 分离用户ID和部门ID
  const userKeys = [];
  const deptKeys = [];
  
  assignedCheckedKeys.value.forEach(key => {
    if (key.startsWith('user_')) {
      userKeys.push(key);
    } else if (key.startsWith('dept_')) {
      deptKeys.push(key);
    }
  });
  
  // 移除用户
  assignedUserIds.value = assignedUserIds.value.filter(
    userId => !userKeys.includes(userId)
  );
  
  // 移除部门
  assignedDeptIds.value = assignedDeptIds.value.filter(
    deptId => !deptKeys.includes(deptId)
  );
  
  // 清空选中
  assignedCheckedKeys.value = [];
};

// 处理搜索
const handleAvailableSearch = () => {
  // 搜索逻辑已在计算属性中实现
};

const handleAssignedSearch = () => {
  // 搜索逻辑已在计算属性中实现
};

// 处理取消
const handleCancel = () => {
  emit('update:visible', false);
  emit('cancel');
};

// 处理确认
const handleConfirm = async () => {
  loading.value = true;
  try {
    // 构建权限数据
    const permissionData = {
      kb_id: props.kbId,
      permissions_data: {
        user_permissions: [],
        department_permissions: []
      }
    };
    
    // 添加用户权限
    assignedUserIds.value.forEach(userId => {
      permissionData.permissions_data.user_permissions.push({
        user_id: userId,
        permission_type: "read" // 默认为只读权限
      });
    });
    
    // 添加部门权限
    assignedDeptIds.value.forEach(deptId => {
      permissionData.permissions_data.department_permissions.push({
        dept_id: deptId,
        permission_type: "read" // 默认为只读权限
      });
    });
    
    // 调用API更新权限数据
    const result = await urlRequest.updateKbPermissionData(permissionData);
    
    if (result.code === 200) {
      emit('confirm', permissionData);
      emit('update:visible', false);
    }
  } catch (error) {
    console.error('更新权限数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 组件挂载时获取数据
onMounted(() => {
  if (props.visible) {
    fetchPermissionData();
  }
});

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    fetchPermissionData();
  }
});

// 处理可用树的选中变化
const handleAvailableCheck = (checkedKeys, { checked, node }) => {
  availableCheckedKeys.value = checkedKeys;
  
  // 如果是部门节点，则全选/取消全选其子元素
  if (!node.isLeaf && node.children && node.children.length > 0) {
    const allChildKeys = getAllChildKeys(node);
    
    if (checked) {
      // 添加所有子节点到选中列表
      allChildKeys.forEach(key => {
        if (!availableCheckedKeys.value.includes(key)) {
          availableCheckedKeys.value.push(key);
        }
      });
    } else {
      // 从选中列表中移除所有子节点
      availableCheckedKeys.value = availableCheckedKeys.value.filter(
        key => !allChildKeys.includes(key)
      );
    }
  }
};

// 处理已分配树的选中变化
const handleAssignedCheck = (checkedKeys, { checked, node }) => {
  assignedCheckedKeys.value = checkedKeys;
  
  // 如果是部门节点，则全选/取消全选其子元素
  if (!node.isLeaf && node.children && node.children.length > 0) {
    const allChildKeys = getAllChildKeys(node);
    
    if (checked) {
      // 添加所有子节点到选中列表
      allChildKeys.forEach(key => {
        if (!assignedCheckedKeys.value.includes(key)) {
          assignedCheckedKeys.value.push(key);
        }
      });
    } else {
      // 从选中列表中移除所有子节点
      assignedCheckedKeys.value = assignedCheckedKeys.value.filter(
        key => !allChildKeys.includes(key)
      );
    }
  }
};

// 获取节点的所有子节点的key
const getAllChildKeys = (node) => {
  const keys = [];
  
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => {
      keys.push(child.key);
      
      if (child.children && child.children.length > 0) {
        keys.push(...getAllChildKeys(child));
      }
    });
  }
  
  return keys;
};
</script>

<style scoped>
.permission-dialog {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.permission-tabs {
  display: flex;
  flex: 1;
  margin-bottom: 20px;
}

.tab-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  overflow: hidden;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
}

.count {
  font-size: 12px;
  color: #86909c;
}

.user-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  max-height: 400px;
}

/* 添加加载容器样式 */
.loading-container {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.tab-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 10px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 自定义树节点样式 */
:deep(.arco-tree-node) {
  padding: 4px 0;
}

:deep(.arco-tree-node-title) {
  font-size: 14px;
}

:deep(.arco-tree-node-indent-unit) {
  width: 16px;
}

:deep(.arco-tree-node-switcher) {
  font-size: 14px;
}
</style>
