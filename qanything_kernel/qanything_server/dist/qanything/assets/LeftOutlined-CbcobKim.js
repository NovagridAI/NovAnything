import{v as e,e as t,as as n,C as a,br as o,c as r,I as u}from"./index-Dnd1wrVz.js";function l(r,u){const{defaultValue:l,value:c=e()}=u||{};let i="function"==typeof r?r():r;void 0!==c.value&&(i=t(c)),void 0!==l&&(i="function"==typeof l?l():l);const s=e(i),f=e(i);return n((()=>{let e=void 0!==c.value?c.value:s.value;u.postState&&(e=u.postState(e)),f.value=e})),a(c,(()=>{s.value=c.value})),[f,function(e){const t=f.value;s.value=e,o(f.value)!==e&&u.onChange&&u.onChange(e,t)}]}var c={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M724 218.3V141c0-6.7-7.7-10.4-12.9-6.3L260.3 486.8a31.86 31.86 0 000 50.3l450.8 352.1c5.3 4.1 12.9.4 12.9-6.3v-77.3c0-4.9-2.3-9.6-6.1-12.6l-360-281 360-281.1c3.8-3 6.1-7.7 6.1-12.6z"}}]},name:"left",theme:"outlined"};function i(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?Object(arguments[t]):{},a=Object.keys(n);"function"==typeof Object.getOwnPropertySymbols&&(a=a.concat(Object.getOwnPropertySymbols(n).filter((function(e){return Object.getOwnPropertyDescriptor(n,e).enumerable})))),a.forEach((function(t){s(e,t,n[t])}))}return e}function s(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}var f=function(e,t){var n=i({},e,t.attrs);return r(u,i({},n,{icon:c}),null)};f.displayName="LeftOutlined",f.inheritAttrs=!1;export{f as L,l as u};
