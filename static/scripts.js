function atualizarRelogio() {
  const agora = new Date();
  document.getElementById("relogio").innerText = agora.toLocaleString('pt-BR');
}
setInterval(atualizarRelogio, 1000);
atualizarRelogio();

function loadPage(event, url) {
  event.preventDefault();
  fetch(url)
    .then(response => response.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const content = doc.querySelector("#conteudo");
      document.querySelector("#conteudo").innerHTML = content.innerHTML;
    });
}
