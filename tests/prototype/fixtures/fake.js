(function(){
  const KEY='fakedb';
  const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}};
  let store=load();
  const listeners=[]; // {coll, path, next, prev:Map}
  const deep=o=>JSON.parse(JSON.stringify(o));
  function snapDoc(path){const d=store[path];return {id:path.split('/').pop(),exists:d!==undefined,data:()=>d===undefined?undefined:deep(d),metadata:{fromCache:false,hasPendingWrites:false}}}
  function collDocs(c){return Object.keys(store).filter(p=>p.split('/').length===2&&p.split('/')[0]===c).sort().map(snapDoc)}
  function deliver(){listeners.forEach(L=>{if(L.dead)return;if(L.coll){const docs=collDocs(L.coll);const cur=new Map(docs.map(d=>[d.id,JSON.stringify(d.data())]));const changes=[];
      docs.forEach((d,i)=>{const pj=L.prev.get(d.id);if(pj===undefined)changes.push({type:'added',doc:d,oldIndex:-1,newIndex:i});else if(pj!==cur.get(d.id))changes.push({type:'modified',doc:d,oldIndex:i,newIndex:i})});
      L.prev.forEach((pj,id)=>{if(!cur.has(id))changes.push({type:'removed',doc:{id,exists:true,data:()=>JSON.parse(pj),metadata:{}},oldIndex:0,newIndex:-1})});
      L.prev=cur;if(changes.length||L.first){L.first=false;L.next({docs,size:docs.length,empty:!docs.length,docChanges:()=>changes,metadata:{fromCache:false,hasPendingWrites:false}})}}})}
  function save(){localStorage.setItem(KEY,JSON.stringify(store));window.__writes=(window.__writes||0)+1;setTimeout(deliver,5)}
  window.addEventListener('storage',e=>{if(e.key===KEY){store=load();deliver()}});
  const MAXB=256*1024;
  function docRef(path){return {id:path.split('/').pop(),path,
    get:async()=>snapDoc(path),
    set:async d=>{const j=JSON.stringify(d);if(j.length>MAXB)throw {code:'invalid_argument',message:'document over 256 KiB'};if(window.__readonly)throw {code:'invalid_argument',message:'not allowed'};store[path]=JSON.parse(j);save()},
    update:async d=>{if(store[path]===undefined)throw {code:'invalid_argument',message:'missing'};store[path]=Object.assign(store[path],deep(d));save()},
    delete:async()=>{delete store[path];save()},
    onSnapshot:(next)=>{const L={path,next};listeners.push(L);setTimeout(()=>next(snapDoc(path)),5);return ()=>{L.dead=true}},
    collection:sub=>collRef(path+'/'+sub)}}
  function collRef(c){return {path:c,doc:id=>docRef(c+'/'+(id||Math.random().toString(36).slice(2))),
    get:async()=>{const docs=collDocs(c);return {docs,size:docs.length,empty:!docs.length,docChanges:()=>docs.map((d,i)=>({type:'added',doc:d,oldIndex:-1,newIndex:i})),metadata:{}}},
    onSnapshot:(next)=>{const L={coll:c,next,prev:new Map(),first:true};listeners.push(L);setTimeout(deliver,5);return ()=>{L.dead=true}},
    where(){return this},orderBy(){return this},limit(){return this}}}
  const db={doc:docRef,collection:collRef};
  const NAMES={u_owner:'Tony Webb',u_sophie:'Sophie Martin',u_alex:'Alex Morgan'};
  const user={isOwner:async()=>!!window.__owner,canEdit:async()=>!!window.__owner,can:async()=>window.__readonly?false:true,
    me:async()=>({id:window.__uid||null,name:NAMES[window.__uid]||'',avatarUrl:'',color:'#888',email:null,isOwner:!!window.__owner,canEdit:!!window.__owner}),
    id:async()=>window.__uid||null,profiles:async ids=>{const o={};(Array.isArray(ids)?ids:[ids]).forEach(id=>o[id]={id,name:NAMES[id]||'',avatarUrl:'',color:'#888',email:null,isMe:id===window.__uid,guest:false});return o},search:async()=>[]};
  const downloads={save:async({filename,data})=>{window.__downloads=(window.__downloads||[]).concat([{filename,size:(data.length||data.size||0)}]);return {status:'saved'}}};
  window.claude={use:async n=>{await new Promise(r=>setTimeout(r,30));return n==='db'?db:n==='user'?user:n==='downloads'?downloads:null}};
})();
