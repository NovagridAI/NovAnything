import{a5 as a}from"./index-Dnd1wrVz.js";const s=a({id:"useBotsChat",state:()=>({QA_List:[],showModal:!1}),actions:{clearQAList(){this.QA_List=[]},setQaList(a){this.QA_List=a},async handleSource(a){const s=await Promise.all(a.map((async a=>{if(!a.pdf_source_info)return a;const s=await fetch(a.pdf_source_info.chunks_nos_url),e=await s.json(),{chunks:i,pageSizes:t}=this.formatChunks(e);return{...a,chunks:i,pageSizes:t}})));this.QA_List[this.QA_List.length-1].source=s},formatChunks(a){let s=[],e=[];return a.forEach((a=>{"normal"===a.chunk_type?a.locations.forEach((i=>{s[i.page_id]||(s[+i.page_id]={page_w:i.page_w,page_h:i.page_h}),e[i.page_id]||(e[i.page_id]=[]),e[i.page_id].push({chunkId:a.chunk_id,lines_box:i.lines,bbox:i.bbox})})):a.locations.forEach((a=>{s[a.page_id]||(s[+a.page_id]={page_w:a.page_w,page_h:a.page_h})}))})),{chunks:[...e],pageSizes:[...s]}}}});export{s as u};
