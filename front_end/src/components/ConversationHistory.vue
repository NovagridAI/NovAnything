<template>
  <div class="conversation-history">
    <div class="history-header">
      <h3 class="history-title">话题</h3>
    </div>

    <div class="history-section" v-if="favoriteItems.length > 0">
      <div class="section-title">收藏</div>
      <div v-for="item in favoriteItems" :key="'fav-' + item.qa_id" class="section-item"
        :class="{ active: selectedConversation === item.qa_id }" @click="selectConversation(item)">
        <icon-star-fill class="item-icon favorite" @click.stop="toggleFavorite(item)" />
        <span>{{ formatTitle(item.query) }}</span>
        <icon-delete class="item-icon delete-icon" @click.stop="deleteConversation(item)" />
      </div>
    </div>

    <div class="history-section" v-if="weeklyItems.length > 0">
      <div class="section-title">本周</div>
      <div v-for="item in weeklyItems" :key="'week-' + item.qa_id" class="section-item"
        :class="{ active: selectedConversation === item.qa_id }" @click="selectConversation(item)">
        <icon-star class="item-icon" @click.stop="toggleFavorite(item)" />
        <span>{{ formatTitle(item.query) }}</span>
        <icon-delete class="item-icon delete-icon" @click.stop="deleteConversation(item)" />
      </div>
    </div>

    <div class="history-section" v-if="monthlyItems.length > 0">
      <div class="section-title">本月</div>
      <div v-for="item in monthlyItems" :key="'month-' + item.qa_id" class="section-item"
        :class="{ active: selectedConversation === item.qa_id }" @click="selectConversation(item)">
        <icon-star class="item-icon" @click.stop="toggleFavorite(item)" />
        <span>{{ formatTitle(item.query) }}</span>
        <icon-delete class="item-icon delete-icon" @click.stop="deleteConversation(item)" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { IconStar, IconStarFill, IconDelete } from '@arco-design/web-vue/es/icon';
import { Message, Modal } from '@arco-design/web-vue';
import urlResquest from '@/services/urlConfig';
import { useHomeChat } from '@/store/useHomeChat';
import { storeToRefs } from 'pinia';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { IChatItemInfo } from '@/utils/types';

const { chatList, chatId, QA_List, qaPageId } = storeToRefs(useHomeChat());
const { addChatList, getChatById, setCurrentQaId, setHistoryList } = useHomeChat();
const { setSelectList } = useKnowledgeBase();
const { knowledgeBaseList } = storeToRefs(useKnowledgeBase());
const { setTempId } = useKnowledgeBase();

const tempList = computed(() => knowledgeBaseList.value.filter(item => item.kb_type === 'temporary'));

console.log(tempList.value, 'tempList');


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
const selectConversation = (item) => {
  console.log(item, 'item');
  const currentTempId = item.kb_ids.find(item => tempList.value.some(temp => temp.kb_id === item));
  if(currentTempId) {
    setTempId(currentTempId);
  }
  changeChat(item);
  selectedConversation.value = item.qa_id;
  setCurrentQaId(item.qa_id);
  emit('select-conversation', item);
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

function addQuestion(q) {
  QA_List.value.push({
    question: q,
    type: 'user',
  });
  // scrollBottom();
}

function addAnswer(
  question: string,
  itemInfo: IChatItemInfo,
  answer: string,
  picList,
  qaId,
  source
) {
  QA_List.value.push({
    answer,
    question,
    itemInfo,
    type: 'ai',
    qaId,
    copied: false,
    like: false,
    unlike: false,
    source: source ? source : [],
    showTools: true,
    picList,
  });
}

// 选择/切换对话
async function changeChat(item) {
  console.log(chatList.value, 'item');
  // 正在问答时禁止操作
  chatId.value = item.qa_id;
  QA_List.value = [];
  qaPageId.value = 1;
  setSelectList([...item.kb_ids]);
  try {
    // const res: any = await resultControl(
    //   await urlResquest.chatDetail({
    //     historyId: chatId.value,
    //     page: qaPageId.value,
    //     pageSize: 50,
    //   })
    // );
    const chat = getChatById(chatId.value);
    // 清除上次监听的dom元素
    // if (props.qaObserveDom !== null) {
    //   props.qaObserver.unobserve(props.qaObserveDom);
    //   emits('setQaObserverDom', null);
    // }
    // chat.list.reverse().forEach(item => {
    //   addQuestion(item.question);
    //   addAnswer(item.question, item.answer, item.picList, item.qaId, item.source);
    // });
    chat.list.forEach(item => {
      if (item.type === 'user') {
        addQuestion(item.question);
      } else if (item.type === 'ai') {
        addAnswer(item.question, item.itemInfo, item.answer, item.picList, item.qaId, item.source);
      }
    });
    // emits('scrollBottom');
    // if (chat.list.length >= 50) {
    //   await nextTick(() => {
    //     // 监听新的dom元素
    //     const eles: any = document.getElementsByClassName('chat-li');
    //     if (eles.length) {
    //       props.qaObserver.observe(eles[0]);
    //       emits('setQaObserverDom', eles[0]);
    //     }
    //   });
    // }
  } catch (e) {
    // message.error(e.msg || '获取问答历史失败');
  }
}


// 使用真实API获取会话历史
const fetchConversationHistory = async () => {
  try {
    // 调用真实API获取问答日志列表
    const response = await urlResquest.getQaLogs({}, {});

    if (response && response.code === 200 && response.data) {
      // 分类会话数据
      categorizeConversations(response.data.qa_logs || []);

      response.data.qa_logs.forEach(item => {
        addChatList(item.qa_id, item.history, item.qa_id);
      });

      const historyList = response.data.qa_logs.map(item => {
        return {
          qa_id: item.qa_id,
          title: item.query,
          kb_ids: item.kb_ids,
        }
      });
      setHistoryList(historyList);
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

// 删除会话
const deleteConversation = async (item) => {
  Modal.warning({
    title: '确认删除',
    content: '确定要删除这个会话吗？此操作不可恢复。',
    okText: '删除',
    cancelText: '取消',
    async onOk() {
      try {
        // 调用删除API
        const response = await urlResquest.deleteQaLog({
          qa_id: item.qa_id
        });

        if (response && response.code === 200) {
          // 从所有列表中移除该项
          favoriteItems.value = favoriteItems.value.filter(i => i.qa_id !== item.qa_id);
          weeklyItems.value = weeklyItems.value.filter(i => i.qa_id !== item.qa_id);
          monthlyItems.value = monthlyItems.value.filter(i => i.qa_id !== item.qa_id);

          // 如果删除的是当前选中的会话，则重置选中状态
          if (selectedConversation.value === item.qa_id) {
            selectConversation(null);
          }

          Message.success('删除成功');
        } else {
          Message.error(response?.msg || '删除失败');
        }
      } catch (error) {
        console.error('删除失败:', error);
        Message.error('删除失败，请稍后重试');
      }
    }
  });
};

// 组件挂载时获取数据
onMounted(() => {
  fetchConversationHistory();
});
</script>

<style scoped lang="scss">
.conversation-history {
  background-color: #F8F8F8;
  border-left: 1px solid #D8D8D8;
  max-width: 279px;
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
  font-weight: 400;
  color: $mainFontColor;
}

.history-section {
  padding: 8px 0;
}

.section-title {
  margin: 8px 16px;
  font-size: 14px;
  color: #86909c;
}

.section-item {
  display: flex;
  align-items: center;
  margin: 6px 16px;
  padding: 6px 16px;
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

.delete-icon {
  margin-left: auto;
  color: #86909c;
  opacity: 0;
  transition: opacity 0.2s;
}

.section-item:hover .delete-icon {
  opacity: 1;
}

.delete-icon:hover {
  color: #f53f3f;
}

.section-item span {
  font-size: 14px;
  color: #1d2129;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}
</style>