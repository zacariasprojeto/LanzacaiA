// static/app.js

// Função para mostrar mensagens simples na tela
function showMessage(msg, type = "info") {
  alert(msg); // depois dá pra trocar por toast bonitinho
}

// LOGIN
async function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById("emailLogin").value.trim();
  const password = document.getElementById("senhaLogin").value.trim();

  if (!email || !password) {
    showMessage("Preencha email e senha.");
    return;
  }

  try {
    const resp = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await resp.json();

    if (data.status === "ok") {
      showMessage("Login realizado com sucesso!");
      // aqui depois você pode redirecionar para um /dashboard, por ex:
      // window.location.href = "/dashboard";
    } else {
      showMessage(data.msg || "Erro ao fazer login.");
    }
  } catch (err) {
    console.error(err);
    showMessage("Falha ao conectar com o servidor.");
  }
}

// CADASTRO
async function handleRegister(event) {
  event.preventDefault();

  const email = document.getElementById("emailLogin").value.trim();
  const password = document.getElementById("senhaLogin").value.trim();

  if (!email || !password) {
    showMessage("Preencha email e senha para cadastrar.");
    return;
  }

  try {
    const resp = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await resp.json();

    if (data.status === "ok") {
      showMessage(
        data.msg ||
          "Cadastro enviado! Aguarde o administrador aprovar seu acesso."
      );
    } else {
      showMessage(data.msg || "Erro ao cadastrar.");
    }
  } catch (err) {
    console.error(err);
    showMessage("Falha ao conectar com o servidor.");
  }
}

// Quando a página carregar, ligar os botões
document.addEventListener("DOMContentLoaded", () => {
  const btnLogin = document.getElementById("btnEntrar");
  const btnCadastrar = document.getElementById("btnCadastrar");

  if (btnLogin) {
    btnLogin.addEventListener("click", handleLogin);
  }

  if (btnCadastrar) {
    btnCadastrar.addEventListener("click", handleRegister);
  }
});
