<template>
  <div class="conversation-history">
    <div class="history-header">
      <h3>话题</h3>
    </div>
    
    <div class="history-section">
      <div class="section-item default-item" @click="selectConversation(null)">
        <icon-message class="item-icon" />
        <span>默认话题</span>
      </div>
    </div>
    
    <div class="history-section" v-if="favoriteItems.length > 0">
      <div class="section-title">收藏</div>
      <div 
        v-for="item in favoriteItems" 
        :key="'fav-' + item.qa_id" 
        class="section-item"
        :class="{ active: selectedConversation === item.qa_id }"
        @click="selectConversation(item.qa_id)"
      >
        <icon-star-fill class="item-icon favorite" @click.stop="toggleFavorite(item)" />
        <span>{{ formatTitle(item.query) }}</span>
      </div>
    </div>
    
    <div class="history-section" v-if="weeklyItems.length > 0">
      <div class="section-title">本周</div>
      <div 
        v-for="item in weeklyItems" 
        :key="'week-' + item.qa_id" 
        class="section-item"
        :class="{ active: selectedConversation === item.qa_id }"
        @click="selectConversation(item.qa_id)"
      >
        <icon-star 
          class="item-icon" 
          @click.stop="toggleFavorite(item)"
        />
        <span>{{ formatTitle(item.query) }}</span>
      </div>
    </div>
    
    <div class="history-section" v-if="monthlyItems.length > 0">
      <div class="section-title">本月</div>
      <div 
        v-for="item in monthlyItems" 
        :key="'month-' + item.qa_id" 
        class="section-item"
        :class="{ active: selectedConversation === item.qa_id }"
        @click="selectConversation(item.qa_id)"
      >
        <icon-star 
          class="item-icon" 
          @click.stop="toggleFavorite(item)"
        />
        <span>{{ formatTitle(item.query) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { IconMessage, IconStar, IconStarFill } from '@arco-design/web-vue/es/icon';
import { Message } from '@arco-design/web-vue';
import urlResquest from '@/services/urlConfig';

// 当前选中的会话
const selectedConversation = ref(null);

// 会话数据
const favoriteItems = ref([]);
const weeklyItems = ref([]);
const monthlyItems = ref([]);

// 格式化标题，截取前20个字符
const formatTitle = (query) => {
  if (!query) return '新对话';
  return query.length > 20 ? query.substring(0, 20) + '...' : query;
};

// 选择会话
const selectConversation = (id) => {
  selectedConversation.value = id;
  emit('select-conversation', id);
};

// 定义事件
const emit = defineEmits(['select-conversation']);

// 分类会话数据
const categorizeConversations = (conversations) => {
  // 清空现有数据
  favoriteItems.value = [];
  weeklyItems.value = [];
  monthlyItems.value = [];
  
  // 获取时间范围
  const now = new Date();
  const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  
  // 分类每条会话
  conversations.forEach(item => {
    // 解析时间戳
    const itemDate = new Date(item.timestamp);
    
    // 优先级：收藏 > 本周 > 本月
    if (item.is_favorite) {
      favoriteItems.value.push(item);
    } else if (itemDate >= oneWeekAgo) {
      weeklyItems.value.push(item);
    } else if (itemDate >= oneMonthAgo) {
      monthlyItems.value.push(item);
    }
  });
};

// 使用真实API获取会话历史
const fetchConversationHistory = async () => {
  try {
    // 调用真实API获取问答日志列表
    const response = await urlResquest.getQaLogs({}, {});
    
    if (response && response.code === 200 && response.data) {
      // 分类会话数据
      categorizeConversations(response.data.qa_logs || []);
    } else {
      console.warn('获取会话历史返回的数据格式不正确:', response);
      Message.error(response?.msg || '获取会话历史失败');
    }
  } catch (error) {
    console.error('获取会话历史失败:', error);
    Message.error('获取会话历史失败，请稍后重试');
  }
};

// 收藏/取消收藏会话
const toggleFavorite = async (item) => {
  try {
    // 调用真实API切换收藏状态
    const response = await urlResquest.toggleQaFavorite({
      qa_id: item.qa_id,
      is_favorite: !item.is_favorite
    });
    
    if (response && response.code === 200) {
      // 更新收藏状态
      item.is_favorite = !item.is_favorite;
      
      // 从所有列表中移除该项
      favoriteItems.value = favoriteItems.value.filter(i => i.qa_id !== item.qa_id);
      weeklyItems.value = weeklyItems.value.filter(i => i.qa_id !== item.qa_id);
      monthlyItems.value = monthlyItems.value.filter(i => i.qa_id !== item.qa_id);
      
      // 重新分类该项
      const now = new Date();
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      const itemDate = new Date(item.timestamp);
      
      if (item.is_favorite) {
        favoriteItems.value.push(item);
      } else if (itemDate >= oneWeekAgo) {
        weeklyItems.value.push(item);
      } else if (itemDate >= oneMonthAgo) {
        monthlyItems.value.push(item);
      }
      
      Message.success(item.is_favorite ? '已收藏' : '已取消收藏');
    } else {
      Message.error(response?.msg || '操作失败');
    }
  } catch (error) {
    console.error('操作失败:', error);
    Message.error('操作失败，请稍后重试');
  }
};

// 组件挂载时获取数据
onMounted(() => {
  fetchConversationHistory();
});
</script>

<style scoped>
.conversation-history {
  background-color: #F8F8F8;
  border-left: 1px solid #D8D8D8;
  padding-left: 16px;
  padding-right: 16px;
  max-width: 280px;
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.history-header {
  padding: 16px;
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #1d2129;
}

.history-section {
  padding: 8px 0;
}

.section-title {
  padding: 8px 16px;
  font-size: 14px;
  color: #86909c;
}

.section-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.section-item:hover {
  background-color: #f2f3f5;
}

.section-item.active {
  background-color: #EEEEEE;
}

.default-item {
  font-weight: 500;
}

.item-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #86909c;
}

.item-icon.favorite {
  color: #ffb400;
}

.section-item span {
  font-size: 14px;
  color: #1d2129;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 