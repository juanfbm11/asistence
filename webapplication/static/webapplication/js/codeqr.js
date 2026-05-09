/**
 * codeqr.js
 * ─────────
 * Maneja:
 *  1. Generación del QR con la URL real del servidor
 *  2. Contador regresivo sincronizado con EXPIRA_EN
 *  3. Polling cada 5 s a /api/qr/<token>/estado/
 *     → actualiza lista de presentes en tiempo real
 *  4. Botón "Regenerar" → llama /api/qr/generar/ y recarga
 *  5. Botón "Copiar enlace"
 *
 * Variables inyectadas desde el template (codeqr.html):
 *   QR_URL, SESION_TOKEN, EXPIRA_EN, segundosRestantes,
 *   TOTAL_ALUMNOS, URL_ESTADO, URL_LISTA_CLASE, CLASE_ID, CSRF_TOKEN
 */

// ── Elementos del DOM ──────────────────────────────────────────────────
const elTimer       = document.getElementById('timerDisplay');
const elBar         = document.getElementById('timerBar');
const elRing        = document.getElementById('ringFill');
const elOverlay     = document.getElementById('expiredOverlay');
const elScanned     = document.getElementById('escaneadosCount');
const elPendientes  = document.getElementById('pendientesCount');
const elPct         = document.getElementById('pctCount');
const elLabel       = document.getElementById('escaneadosLabel');
const elList        = document.getElementById('scannedList');
const elFecha       = document.getElementById('fechaHoy');
const elHora        = document.getElementById('horaHoy');

// Circunferencia del ring SVG (radio 45)
const CIRCUNFERENCIA = 2 * Math.PI * 45;   // ≈ 282.7
const DURACION_SEG   = 120;                 // 2 minutos

// ── 1. Generar el QR ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    generarQR();
});

function generarQR() {
    const qrDiv = document.getElementById('qrCanvas');

    if (!qrDiv) {
        console.error('No existe #qrCanvas');
        return;
    }

    if (typeof QR_URL === 'undefined' || !QR_URL) {
        console.error('QR_URL no definida');
        return;
    }

    if (typeof QRCode === 'undefined') {
        console.error('La librería QRCode no cargó');
        return;
    }

    qrDiv.innerHTML = '';

    new QRCode(qrDiv, {
        text: QR_URL,
        width: 220,
        height: 220,
        colorDark: '#0f2044',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.H
    });

    console.log('QR generado correctamente');
}

// ── 2. Fecha y hora actuales ───────────────────────────────────────────
function actualizarReloj() {
    const ahora = new Date();
    if (elFecha) {
        elFecha.textContent = ahora.toLocaleDateString('es-CO', {
            day: '2-digit', month: 'long', year: 'numeric'
        });
    }
    if (elHora) {
        elHora.textContent = ahora.toLocaleTimeString('es-CO', {
            hour: '2-digit', minute: '2-digit'
        });
    }
}
actualizarReloj();
setInterval(actualizarReloj, 1000);

// ── 3. Contador regresivo ──────────────────────────────────────────────
function formatearTiempo(seg) {
    const m = Math.floor(seg / 60);
    const s = seg % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function actualizarTimer(seg) {
    if (!elTimer) return;

    elTimer.textContent = formatearTiempo(seg);

    const pct  = seg / DURACION_SEG;           // 1 → 0
    const offset = CIRCUNFERENCIA * (1 - pct); // 0 → CIRCUNFERENCIA

    if (elRing) {
        elRing.style.strokeDasharray  = CIRCUNFERENCIA;
        elRing.style.strokeDashoffset = offset;
        elRing.style.stroke = seg > 30 ? '#3b74f5' : seg > 10 ? '#f5a623' : '#e8445a';
    }
    if (elBar) {
        elBar.style.width = `${pct * 100}%`;
        elBar.style.background = seg > 30 ? '#3b74f5' : seg > 10 ? '#f5a623' : '#e8445a';
    }
}

let countdownInterval = null;

function iniciarCountdown() {
    clearInterval(countdownInterval);

    // Calcular segundos restantes en base al timestamp real del servidor
    function calcSeg() {
        if (typeof EXPIRA_EN === 'undefined') return 0;
        return Math.max(0, Math.round((EXPIRA_EN - Date.now()) / 1000));
    }

    function tick() {
        const seg = calcSeg();
        actualizarTimer(seg);

        if (seg <= 0) {
            clearInterval(countdownInterval);
            mostrarExpirado();
        }
    }

    tick();
    countdownInterval = setInterval(tick, 1000);
}

function mostrarExpirado() {
    if (elOverlay) elOverlay.style.display = 'flex';
    if (elTimer)   elTimer.textContent = '0:00';
    clearInterval(pollingInterval);
}

// ── 4. Polling del estado (cada 5 s) ──────────────────────────────────
let pollingInterval = null;

function actualizarPresentes(data) {
    const escaneados = data.total_escaneados || 0;
    const total      = data.total_clase      || TOTAL_ALUMNOS;
    const pendientes = Math.max(0, total - escaneados);
    const pct        = total > 0 ? Math.round(escaneados / total * 100) : 0;

    if (elScanned)   elScanned.textContent   = escaneados;
    if (elPendientes) elPendientes.textContent = pendientes;
    if (elPct)       elPct.textContent       = `${pct}%`;
    if (elLabel)     elLabel.textContent     = `${escaneados} / ${total}`;

    // Lista de presentes
    if (elList && data.presentes) {
        if (data.presentes.length === 0) {
            elList.innerHTML = `
                <div class="empty-state">
                    <div style="font-size:32px;margin-bottom:8px">📱</div>
                    <div>Esperando escaneos...</div>
                </div>`;
        } else {
            elList.innerHTML = data.presentes.map(p => `
                <div class="scanned-item" style="
                    display:flex;align-items:center;gap:10px;
                    padding:8px 10px;border-radius:8px;
                    background:rgba(0,196,154,.08);margin-bottom:6px">
                    <div style="
                        width:32px;height:32px;border-radius:50%;
                        background:#00c49a;color:#fff;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:12px;flex-shrink:0">
                        ${p.nombre[0]}${p.apellido[0]}
                    </div>
                    <div>
                        <div style="font-weight:600;font-size:13px;color:#0f2044">
                            ${p.nombre} ${p.apellido}
                        </div>
                        <div style="font-size:11px;color:#8a97b4">${p.email}</div>
                    </div>
                    <div style="margin-left:auto;font-size:16px">✅</div>
                </div>
            `).join('');
        }
    }

    // Si sesión expiró en el servidor, mostrar overlay
    if (data.expirada) {
        mostrarExpirado();
    }
}

async function pollEstado() {
    if (typeof URL_ESTADO === 'undefined' || !SESION_TOKEN) return;
    try {
        const res  = await fetch(URL_ESTADO, { credentials: 'same-origin' });
        if (!res.ok) return;
        const data = await res.json();
        actualizarPresentes(data);
    } catch (e) {
        console.warn('Error en polling:', e);
    }
}

function iniciarPolling() {
    clearInterval(pollingInterval);
    pollEstado();                            // llamada inmediata al cargar
    pollingInterval = setInterval(pollEstado, 5000);
}

// ── 5. Regenerar código ────────────────────────────────────────────────
async function regenerar() {
    if (typeof CLASE_ID === 'undefined') return;

    try {
        const res = await fetch('/api/qr/generar/', {
            method:  'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  CSRF_TOKEN,
            },
            body: JSON.stringify({ clase_id: CLASE_ID, regenerar: true }),
        });

        if (!res.ok) { console.error('Error al regenerar'); return; }

        // Recargar la página para mostrar el nuevo QR con los datos actualizados
        window.location.reload();
    } catch (e) {
        console.error('Error al regenerar QR:', e);
    }
}

// ── 6. Copiar enlace ───────────────────────────────────────────────────
function copiarLink() {
    if (typeof QR_URL === 'undefined') return;
    navigator.clipboard.writeText(QR_URL).then(() => {
        const btn = document.querySelector('.qr-btn-secondary');
        if (btn) {
            btn.textContent = '✅ Copiado';
            setTimeout(() => { btn.textContent = '🔗 Copiar enlace'; }, 2000);
        }
    }).catch(() => {
        prompt('Copia este enlace:', QR_URL);
    });
}

// ── Init ───────────────────────────────────────────────────────────────
if (typeof SESION_TOKEN !== 'undefined' && SESION_TOKEN) {
    iniciarCountdown();
    iniciarPolling();
}
