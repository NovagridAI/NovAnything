<template>
  <div class="edit-detail">
    <BotDetailEdit ref="botDetailEditRef" />
    <div class="bots-chat-page">
      <Chat :bot-info="curBot" chat-type="edit" />
    </div>
  </div>
</template>
<script lang="ts" setup>
import BotDetailEdit from '@/components/Bots/BotDetailEdit.vue';
import Chat from '@/components/Bots/Chat.vue';
import { useBots } from '@/store/useBots';
const { curBot } = storeToRefs(useBots());

const botDetailEditRef = ref<InstanceType<typeof BotDetailEdit>>();

provide('checkSettingOk', () => botDetailEditRef.value.handleOk(null, '模型配置已自动保存'));
</script>
<style lang="scss" scoped>
.edit-detail {
  width: 100%;
  height: calc(100vh - 64px - 22px - 66px);
  display: flex;
  justify-content: space-between;
  .bots-chat-page {
    width: 42%;
  }
}
</style>
<style lang="scss">
//.edit-detail {
//  .chat {
//    height: calc(100vh - 64px - 22px - 66px - 52px - 10px - 80px);
//  }
//}
</style>
