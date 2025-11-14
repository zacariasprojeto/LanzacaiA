// static/app.js

let isRegisterMode = false; // false = login, true = cadastro

function setAuthMessage(msg, type = "info") {
  const el = document.getElementById("authMsg");
  if (!el) return;
  el.textContent = msg || "";
  el.style.color =
    type === "error" ? "#ff6b6b" : type === "success" ? "#00ff88" : "#cccccc";
}

function toggleMode() {
  const btnLogin = document.getElementById("loginBtn");
  const btnToggle = document.getElementById("showRegister");

  if (!btnLogin || !btnToggle) return;

  isRegisterMode = !isRegisterMode;

  if (isRegisterMode) {
    btnLogin.textContent = "Enviar cadastro";
    btnToggle.textContent = "Já tenho conta";
    setAuthMessage("Preencha email e senha para solicitar acesso.");
  } else {
    btnLogin.textContent = "Entrar";
    btnToggle.textContent = "Cadastrar";
    setAuthMessage("");
  }
}

async function doLogin(email, password) {
  const resp = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await resp.json();
  if (data.status === "ok") {
    setAuthMessage("Login realizado com sucesso!", "success");

    // Esconde tela de login e mostra sistema
    const authContainer = document.getElementById("authContainer");
    const mainContainer = document.getElementById("containerPrincipal");
    const nomeUsuario = document.getElementById("nomeUsuario");

    if (authContainer) authContainer.style.display = "none";
    if (mainContainer) mainContainer.style.display = "block";
    if (nomeUsuario)
      nomeUsuario.textContent = `Olá, ${data.user?.email || "usuário"}!`;

    // aqui depois você pode carregar apostas do backend (/api/bets, etc)
  } else {
    setAuthMessage(data.msg || "Erro ao fazer login.", "error");
  }
}

async function doRegister(email, password) {
  const resp = await fetch("/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await resp.json();
  if (data.status === "ok") {
    setAuthMessage(
      data.msg ||
        "Cadastro enviado! Aguarde o administrador aprovar seu acesso.",
      "success"
    );
  } else {
    setAuthMessage(data.msg || "Erro ao cadastrar.", "error");
  }
}

function setupAuthEvents() {
  const emailInput = document.getElementById("email");
  const passInput = document.getElementById("password");
  const btnLogin = document.getElementById("loginBtn");
  const btnToggle = document.getElementById("showRegister");

  if (!emailInput || !passInput || !btnLogin || !btnToggle) {
    console.warn("Elementos de autenticação não encontrados no DOM.");
    return;
  }

  btnLogin.addEventListener("click", async (e) => {
    e.preventDefault();
    const email = emailInput.value.trim();
    const password = passInput.value.trim();

    if (!email || !password) {
      setAuthMessage("Preencha email e senha.", "error");
      return;
    }

    try {
      if (isRegisterMode) {
        await doRegister(email, password);
      } else {
        await doLogin(email, password);
      }
    } catch (err) {
      console.error(err);
      setAuthMessage("Falha ao conectar com o servidor.", "error");
    }
  });

  btnToggle.addEventListener("click", (e) => {
    e.preventDefault();
    toggleMode();
  });

  // Enter dispara a ação principal (login/cadastro)
  passInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      btnLogin.click();
    }
  });
}

function setupLogoutAndAdmin() {
  const btnLogout = document.getElementById("btnLogout");
  const btnAdminToggle = document.getElementById("btnAdminToggle");
  const adminPanel = document.getElementById("adminPanel");
  const authContainer = document.getElementById("authContainer");
  const mainContainer = document.getElementById("containerPrincipal");

  if (btnLogout) {
    btnLogout.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch("/api/logout", { method: "POST" }).catch(() => {});
      } catch (_) {}
      if (mainContainer) mainContainer.style.display = "none";
      if (authContainer) authContainer.style.display = "flex";
      setAuthMessage("Você saiu da conta.");
    });
  }

  if (btnAdminToggle && adminPanel) {
    btnAdminToggle.addEventListener("click", (e) => {
      e.preventDefault();
      adminPanel.style.display =
        adminPanel.style.display === "none" || !adminPanel.style.display
          ? "block"
          : "none";
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupAuthEvents();
  setupLogoutAndAdmin();
  setAuthMessage("");
});
