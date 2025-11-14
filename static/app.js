// reads server-injected env
const SUPABASE_URL = window.__ENV__.SUPABASE_URL || "";
const SUPABASE_ANON_KEY = window.__ENV__.SUPABASE_ANON_KEY || "";

function showToast(msg, t=3000){
  const el = document.getElementById('toast'); el.textContent = msg; el.classList.add('show');
  setTimeout(()=> el.classList.remove('show'), t);
}

async function apiPost(path, data){
  const r = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(data)});
  return r.json();
}
async function apiGet(path){ const r = await fetch(path,{credentials:'same-origin'}); return r.json(); }

document.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('loginBtn').addEventListener('click', async ()=>{
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if(!email||!password){ document.getElementById('authMsg').textContent='Preencha email e senha'; return; }
    document.getElementById('authMsg').textContent='Entrando...';
    const resp = await apiPost('/api/login', {email,password});
    if(resp.status==='ok'){ document.getElementById('authMsg').textContent=''; showApp(resp.user); showToast('Bem-vindo!'); }
    else { document.getElementById('authMsg').textContent = resp.msg || 'Erro'; }
  });

  document.getElementById('showRegister').addEventListener('click', async ()=>{
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if(!email||!password){ document.getElementById('authMsg').textContent='Preencha email e senha'; return; }
    document.getElementById('authMsg').textContent='Enviando cadastro...';
    const resp = await apiPost('/api/register', {email,password});
    document.getElementById('authMsg').textContent = resp.msg || resp.status;
  });

  document.getElementById('btnLogout').addEventListener('click', async ()=>{
    await apiPost('/api/logout',{}); location.reload();
  });

  document.getElementById('btnAdminToggle').addEventListener('click', async ()=>{
    const panel = document.getElementById('adminPanel');
    if(panel.style.display==='none' || panel.style.display===''){
      const resp = await apiGet('/api/pending_users');
      if(resp.status==='ok'){ renderPending(resp.pending||[]); panel.style.display='block'; }
      else showToast(resp.msg||'Sem permissão',3000);
    } else panel.style.display='none';
  });

  restoreSession();
});

async function restoreSession(){
  const s = await apiGet('/api/session');
  if(s && s.user){ showApp(s.user); }
}

function showApp(user){
  document.getElementById('authContainer').style.display='none';
  document.getElementById('containerPrincipal').style.display='block';
  document.getElementById('nomeUsuario').textContent = `Olá, ${user.email}`;
  loadBetsFromSupabase();
}

function renderPending(list){
  const el = document.getElementById('pendingList');
  if(!list || list.length===0){ el.innerHTML = '<div>Nenhum usuário pendente</div>'; return; }
  el.innerHTML = list.map(u => `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.06)"><div>${u.email}</div><div><button onclick="approveUser('${u.email}')">Aprovar</button></div></div>`).join('');
}

async function approveUser(email){
  const resp = await apiPost('/api/approve_user', {email});
  if(resp.status==='ok'){ showToast('Usuário aprovado'); const r = await apiGet('/api/pending_users'); renderPending(r.pending||[]); }
  else showToast(resp.msg||'Erro');
}

async function loadBetsFromSupabase(){
  if(!SUPABASE_URL || !SUPABASE_ANON_KEY){ loadExampleData(); showToast('Supabase não configurado no front — dados de exemplo',3000); return; }
  try {
    const base = SUPABASE_URL.replace(/\/$/,'') + '/rest/v1';
    const ind = await fetch(`${base}/individuais?select=*&order=value_expected.desc`, {headers:{apikey:SUPABASE_ANON_KEY,Authorization:`Bearer ${SUPABASE_ANON_KEY}`}}).then(r=>r.json());
    const mult = await fetch(`${base}/multiplas?select=*`, {headers:{apikey:SUPABASE_ANON_KEY,Authorization:`Bearer ${SUPABASE_ANON_KEY}`}}).then(r=>r.json());
    renderBets(ind || [], mult || []);
  } catch(e){ console.error(e); loadExampleData(); showToast('Erro Supabase — dados de exemplo',3000); }
}

function renderBets(ind, mult){
  const all = [...ind,...mult]; all.sort((a,b)=> (b.value_expected||b.valor_esperado||0) - (a.value_expected||a.valor_esperado||0));
  const top = all.slice(0,5);
  document.getElementById('topApostas').innerHTML = (top||[]).map(makeCard).join('');
  document.getElementById('gridApostasSeguras').innerHTML = (ind||[]).filter(i=> (i.value_expected||0) > 0.25 && (i.probabilidade||0) > 0.7).map(makeCard).join('');
  document.getElementById('gridMultiplas').innerHTML = (mult||[]).map(makeCard).join('');
  document.getElementById('gridTodasApostas').innerHTML = (ind||[]).map(makeCard).join('');
}
function makeCard(a){ if(a.jogos){ return `<div class="cartao-aposta"><div class="cabecalho-aposta"><h3>Múltipla</h3></div></div>`; } return `<div class="cartao-aposta"><div class="cabecalho-aposta"><h3>${a.match||a.partida||'Partida'}</h3></div></div>`; }
function loadExampleData(){ renderBets([{id:1,match:'Flamengo x Palmeiras',value_expected:0.5,probabilidade:0.82,bet_type:'Mais de 2.5',odds:{betano:{valor:1.95}}}],[]); }
