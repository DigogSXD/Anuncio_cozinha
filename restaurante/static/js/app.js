/* ================================================================
   app.js — Scripts globais do RestaurantePro
   Carregado em todas as páginas admin via base.html
   ================================================================ */

'use strict';

// ── Auto-fecha alertas Bootstrap após 4 segundos ─────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 4000);
  });
});

// ── Confirmação genérica via data-confirm ────────────────────────
// Uso: <button data-confirm="Tem certeza?">Excluir</button>
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-confirm]');
  if (!btn) return;
  const msg = btn.dataset.confirm || 'Tem certeza?';
  if (!confirm(msg)) e.preventDefault();
});

// ── Preview de imagem antes do upload ───────────────────────────
// Adiciona automaticamente a qualquer <input type="file" data-preview="idDoImg">
document.addEventListener('change', (e) => {
  const input = e.target;
  if (input.type !== 'file' || !input.dataset.preview) return;
  const previewEl = document.getElementById(input.dataset.preview);
  if (!previewEl || !input.files[0]) return;
  const url = URL.createObjectURL(input.files[0]);
  previewEl.src = url;
  previewEl.style.display = 'block';
});

// ── Progresso de upload para formulários com enctype multipart ───
document.addEventListener('submit', (e) => {
  const form = e.target;
  if (form.enctype !== 'multipart/form-data') return;

  const progressBar = form.querySelector('.upload-progress');
  if (!progressBar) return;

  const bar = progressBar.querySelector('.progress-bar');
  progressBar.style.display = 'block';

  const xhr = new XMLHttpRequest();
  xhr.open(form.method || 'POST', form.action);

  xhr.upload.addEventListener('progress', (ev) => {
    if (ev.lengthComputable) {
      const pct = Math.round((ev.loaded / ev.total) * 100);
      bar.style.width = pct + '%';
      bar.textContent = pct + '%';
    }
  });

  xhr.addEventListener('load', () => {
    // Redireciona para a URL de resposta (Flask redireciona após POST)
    if (xhr.responseURL) window.location.href = xhr.responseURL;
  });

  xhr.send(new FormData(form));
  e.preventDefault();
});

// ── Formata inputs de preço enquanto o usuário digita ────────────
document.addEventListener('input', (e) => {
  const el = e.target;
  if (!el.classList.contains('input-preco')) return;
  // Remove tudo que não seja dígito ou vírgula/ponto
  let val = el.value.replace(/[^\d,\.]/g, '');
  el.value = val;
});

// ── Tooltip Bootstrap (inicialização global) ─────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    bootstrap.Tooltip.getOrCreateInstance(el);
  });
});

// ── Helper: exibe toast simples ──────────────────────────────────
// Uso: window.showToast('Salvo!', 'success')
window.showToast = function(msg, tipo = 'success') {
  const container = document.getElementById('toast-container') ||
    (() => {
      const el = document.createElement('div');
      el.id = 'toast-container';
      el.className = 'position-fixed bottom-0 end-0 p-3';
      el.style.zIndex = 1100;
      document.body.appendChild(el);
      return el;
    })();

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-bg-${tipo} border-0`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body fw-semibold">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toastEl);
  const t = new bootstrap.Toast(toastEl, { delay: 3000 });
  t.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
};
