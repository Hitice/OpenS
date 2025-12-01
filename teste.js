// teste.js
// Não precisa do require('node-fetch') se Node >=18

async function testar() {
  // 1️⃣ Fazer login
  const loginResp = await fetch("http://127.0.0.1:5000/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "admin@opens.com", senha: "opens2025" })
  });

  const loginData = await loginResp.json();
  if (!loginResp.ok) {
    console.error("Erro no login:", loginData);
    return;
  }

  const token = loginData.access_token;
  console.log("JWT obtido:", token);

  // 2️⃣ Testar rota protegida com token no header
  const dashResp = await fetch("http://127.0.0.1:5000/dashboard", {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  if (dashResp.ok) {
    const html = await dashResp.text();
    console.log("Dashboard HTML recebido:");
    console.log(html.substring(0, 300) + "..."); // mostra só os 300 primeiros chars
  } else {
    console.error("Erro ao acessar dashboard:", dashResp.status);
  }
}

testar();
