import{m as o,q as e,ck as t,s as n,al as r,aq as a,d as i,z as l,v as s,aY as d,t as p,x as c,G as u,c as g,H as v,b_ as m,aN as x,b0 as $,Q as b,af as h}from"./index-Dnd1wrVz.js";import{y as f,P as C,_ as y,t as P,q as k}from"./index-BOQF8sB2.js";const w=o=>{const{componentCls:e,popoverBg:t,popoverColor:a,width:i,fontWeightStrong:l,popoverPadding:s,boxShadowSecondary:d,colorTextHeading:p,borderRadiusLG:c,zIndexPopup:u,marginXS:g,colorBgElevated:v}=o;return[{[e]:n(n({},r(o)),{position:"absolute",top:0,left:{_skip_check_:!0,value:0},zIndex:u,fontWeight:"normal",whiteSpace:"normal",textAlign:"start",cursor:"auto",userSelect:"text","--antd-arrow-background-color":v,"&-rtl":{direction:"rtl"},"&-hidden":{display:"none"},[`${e}-content`]:{position:"relative"},[`${e}-inner`]:{backgroundColor:t,backgroundClip:"padding-box",borderRadius:c,boxShadow:d,padding:s},[`${e}-title`]:{minWidth:i,marginBottom:g,color:p,fontWeight:l},[`${e}-inner-content`]:{color:a}})},f(o,{colorBg:"var(--antd-arrow-background-color)"}),{[`${e}-pure`]:{position:"relative",maxWidth:"none",[`${e}-content`]:{display:"inline-block"}}}]},S=o=>{const{componentCls:e}=o;return{[e]:C.map((t=>{const n=o[`${t}-6`];return{[`&${e}-${t}`]:{"--antd-arrow-background-color":n,[`${e}-inner`]:{backgroundColor:n},[`${e}-arrow`]:{background:"transparent"}}}}))}},z=o=>{const{componentCls:e,lineWidth:t,lineType:n,colorSplit:r,paddingSM:a,controlHeight:i,fontSize:l,lineHeight:s,padding:d}=o,p=i-Math.round(l*s),c=p/2,u=p/2-t,g=d;return{[e]:{[`${e}-inner`]:{padding:0},[`${e}-title`]:{margin:0,padding:`${c}px ${g}px ${u}px`,borderBottom:`${t}px ${n} ${r}`},[`${e}-inner-content`]:{padding:`${a}px ${g}px`}}}},B=o("Popover",(o=>{const{colorBgElevated:n,colorText:r,wireframe:a}=o,i=e(o,{popoverBg:n,popoverColor:r,popoverPadding:12});return[w(i),S(i),a&&z(i),t(i,"zoom-big")]}),(o=>{let{zIndexPopupBase:e}=o;return{zIndexPopup:e+30,width:177}})),A=a(i({compatConfig:{MODE:3},name:"APopover",inheritAttrs:!1,props:l(n(n({},k()),{content:h(),title:h()}),n(n({},P()),{trigger:"hover",placement:"top",mouseEnterDelay:.1,mouseLeaveDelay:.1})),setup(o,e){let{expose:t,slots:n,attrs:r}=e;const a=s();d(void 0===o.visible),t({getPopupDomNode:()=>{var o,e;return null===(e=null===(o=a.value)||void 0===o?void 0:o.getPopupDomNode)||void 0===e?void 0:e.call(o)}});const{prefixCls:i,configProvider:l}=p("popover",o),[h,f]=B(i),C=c((()=>l.getPrefixCls())),P=()=>{var e,t;const{title:r=$(null===(e=n.title)||void 0===e?void 0:e.call(n)),content:a=$(null===(t=n.content)||void 0===t?void 0:t.call(n))}=o,l=!!(Array.isArray(r)?r.length:r),s=!!(Array.isArray(a)?a.length:r);return l||s?g(b,null,[l&&g("div",{class:`${i.value}-title`},[r]),g("div",{class:`${i.value}-inner-content`},[a])]):null};return()=>{const e=u(o.overlayClassName,f.value);return h(g(y,v(v(v({},x(o,["title","content"])),r),{},{prefixCls:i.value,ref:a,overlayClassName:e,transitionName:m(C.value,"zoom-big",o.transitionName),"data-popover-inject":!0}),{title:P,default:n.default}))}}}));export{A as _};
