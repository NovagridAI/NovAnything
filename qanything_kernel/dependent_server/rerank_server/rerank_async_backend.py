from transformers import AutoTokenizer
from copy import deepcopy
from typing import List
import asyncio
from qanything_kernel.configs.model_config import LOCAL_RERANK_MAX_LENGTH, \
    LOCAL_RERANK_BATCH, LOCAL_RERANK_PATH
from qanything_kernel.utils.general_utils import get_time, get_time_async
from onnxruntime import SessionOptions, GraphOptimizationLevel, InferenceSession
from concurrent.futures import ThreadPoolExecutor
from qanything_kernel.utils.custom_log import rerank_logger
import numpy as np

def sigmoid(x):
    x = x.astype('float32')
    scores = 1/(1+np.exp(-x))
    scores = np.clip(1.5*(scores-0.5)+0.5, 0, 1)
    return scores

class RerankAsyncBackend:
    def __init__(self, model_path, use_cpu=True, num_threads=4):
        self.use_cpu = use_cpu
        self.overlap_tokens = 80
        self.max_length = LOCAL_RERANK_MAX_LENGTH
        self.return_tensors = "np"
        # 创建一个ONNX Runtime会话设置，使用GPU执行
        sess_options = SessionOptions()
        sess_options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 0
        sess_options.inter_op_num_threads = 0
        self.batch_size = LOCAL_RERANK_BATCH  # 批处理大小

        if use_cpu:
            providers = ['CPUExecutionProvider']
            self.executor = ThreadPoolExecutor(max_workers=num_threads)
        else:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            self.executor = ThreadPoolExecutor(max_workers=num_threads)

        self.session = InferenceSession(model_path, sess_options, providers=providers)
        self._tokenizer = AutoTokenizer.from_pretrained(LOCAL_RERANK_PATH, use_fast=True)
        self.spe_id = self._tokenizer.sep_token_id

        self.queue = asyncio.Queue()
        asyncio.create_task(self.process_queue())

    @get_time
    def rerank_inference(self, batch):
        rerank_logger.info(f"rerank shape: {batch['attention_mask'].shape}")
        # 准备输入数据
        inputs = {self.session.get_inputs()[i].name: batch[name]
                  for i, name in enumerate(['input_ids', 'attention_mask', 'token_type_ids'])
                  if name in batch}

        # 执行推理 输出为logits
        result = self.session.run(None, inputs)  # None表示获取所有输出
        # debug_logger.info(f"rerank result: {result}")

        # 应用sigmoid函数
        sigmoid_scores = sigmoid(np.array(result[0]))

        return sigmoid_scores.reshape(-1).tolist()

    def merge_inputs(self, chunk1_raw, chunk2):
        chunk1 = deepcopy(chunk1_raw)

        # 在 chunk1 的末尾添加分隔符
        chunk1['input_ids'].append(self.spe_id)
        chunk1['attention_mask'].append(1)  # 为分隔符添加 attention mask

        # 添加 chunk2 的内容
        chunk1['input_ids'].extend(chunk2['input_ids'])
        chunk1['attention_mask'].extend(chunk2['attention_mask'])

        # 在整个序列的末尾再添加一个分隔符
        chunk1['input_ids'].append(self.spe_id)
        chunk1['attention_mask'].append(1)  # 为最后的分隔符添加 attention mask

        if 'token_type_ids' in chunk1:
            # 为 chunk2 和两个分隔符添加 token_type_ids
            token_type_ids = [1 for _ in range(len(chunk2['token_type_ids']) + 2)]
            chunk1['token_type_ids'].extend(token_type_ids)

        return chunk1

    def tokenize_preproc(self, query: str, passages: List[str]):
        query_inputs = self._tokenizer.encode_plus(query, truncation=False, padding=False)
        max_passage_inputs_length = self.max_length - len(query_inputs['input_ids']) - 2  # 减2是因为添加了两个分隔符

        assert max_passage_inputs_length > 10
        overlap_tokens = min(self.overlap_tokens, max_passage_inputs_length * 2 // 7)

        # 组[query, passage]对
        merge_inputs = []
        merge_inputs_idxs = []
        for pid, passage in enumerate(passages):
            passage_inputs = self._tokenizer.encode_plus(passage, truncation=False, padding=False,
                                                         add_special_tokens=False)
            passage_inputs_length = len(passage_inputs['input_ids'])

            if passage_inputs_length <= max_passage_inputs_length:
                if passage_inputs['attention_mask'] is None or len(passage_inputs['attention_mask']) == 0:
                    continue
                qp_merge_inputs = self.merge_inputs(query_inputs, passage_inputs)
                merge_inputs.append(qp_merge_inputs)
                merge_inputs_idxs.append(pid)
            else:
                start_id = 0
                while start_id < passage_inputs_length:
                    end_id = start_id + max_passage_inputs_length
                    sub_passage_inputs = {k: v[start_id:end_id] for k, v in passage_inputs.items()}
                    start_id = end_id - overlap_tokens if end_id < passage_inputs_length else end_id

                    qp_merge_inputs = self.merge_inputs(query_inputs, sub_passage_inputs)
                    merge_inputs.append(qp_merge_inputs)
                    merge_inputs_idxs.append(pid)

        return merge_inputs, merge_inputs_idxs

    @get_time_async
    async def get_rerank_async(self, query: str, passages: List[str]):
        tot_batches, merge_inputs_idxs_sort = self.tokenize_preproc(query, passages)

        futures = []
        mini_batch = 1  # 设置mini_batch为1
        for i in range(0, len(tot_batches), mini_batch):
            future = asyncio.Future()
            futures.append(future)
            await self.queue.put((tot_batches[i:i + mini_batch], future))

        results = await asyncio.gather(*futures)
        tot_scores = [score for batch_scores in results for score in batch_scores]

        merge_tot_scores = [0 for _ in range(len(passages))]
        for pid, score in zip(merge_inputs_idxs_sort, tot_scores):
            merge_tot_scores[pid] = max(merge_tot_scores[pid], score)

        return merge_tot_scores

    async def process_queue(self):
        while True:
            batch_items = []
            futures = []

            try:
                while len(batch_items) < self.batch_size:
                    batch, future = await asyncio.wait_for(self.queue.get(), timeout=0.01)
                    batch_items.extend(batch)
                    futures.append((future, len(batch)))
            except asyncio.TimeoutError:
                pass

            if batch_items:
                loop = asyncio.get_running_loop()
                input_batch = self._tokenizer.pad(
                    batch_items,
                    padding=True,
                    max_length=None,
                    pad_to_multiple_of=None,
                    return_tensors=self.return_tensors
                )
                result = await loop.run_in_executor(self.executor, self.rerank_inference, input_batch)

                start = 0
                for future, item_count in futures:
                    end = start + item_count
                    future.set_result(result[start:end])
                    start = end
            else:
                await asyncio.sleep(0.1)

    async def get_rerank(self, query: str, passages: List[str]):
        return await self.get_rerank_async(query, passages)
