document.addEventListener('DOMContentLoaded', () => {
    const DURATION = 120; 
    let timeLeft = DURATION;
    let timerInterval;
    let pollingInterval;
    let qrCode;
    let escaneados = 0;
    const totalAlumnos = 28;

    const timerDisplay = document.getElementById('timerDisplay');
    const ringFill = document.getElementById('ringFill');
    const timerBar = document.getElementById('timerBar');
    const qrFrameInner = document.getElementById('qrFrameInner');
    const qrCanvasPlaceholder = document.getElementById('qrCanvas');
    const codigoSesionEl = document.getElementById('codigoSesion');
    const fechaHoyEl = document.getElementById('fechaHoy');
    const horaHoyEl = document.getElementById('horaHoy');
    const scannedList = document.getElementById('scannedList');
    const escaneadosCountEl = document.getElementById('escaneadosCount');
    const escaneadosLabelEl = document.getElementById('escaneadosLabel');
    const pctCountEl = document.getElementById('pctCount');

    function init() {
        updateDateTime();
        generateSessionCode();
        startTimer();
        renderQR();
        startPolling(); // Iniciar polling real
    }

    function updateDateTime() {
        const now = new Date();
        const options = { day: 'numeric', month: 'long', year: 'numeric' };
        if (fechaHoyEl) fechaHoyEl.textContent = now.toLocaleDateString('es-ES', options);
        if (horaHoyEl) horaHoyEl.textContent = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    }

    function generateSessionCode() {
        const id = Math.random().toString(36).substring(2, 8).toUpperCase();
        if (codigoSesionEl) codigoSesionEl.textContent = `#HIS-${id}`;
    }

    function renderQR() {
        const sessionId = codigoSesionEl ? codigoSesionEl.textContent.replace('#', '') : 'TEMP';
        const url = `${window.location.origin}/asistencia/registrar/${sessionId}`;

        if (qrCode) {
            qrFrameInner.innerHTML = '';
            reconstructFrame();
        }

        if (qrCanvasPlaceholder) qrCanvasPlaceholder.style.display = 'none';

        qrCode = new QRCode(qrFrameInner, {
            text: url,
            width: 200,
            height: 200,
            colorDark: "#0f2044",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
        
        setTimeout(() => {
            const generated = qrFrameInner.querySelector('img, canvas');
            if (generated) {
                generated.style.display = 'block';
                generated.style.margin = '0 auto';
                generated.style.borderRadius = '8px';
            }
        }, 50);
    }

    function reconstructFrame() {
        ['tl', 'tr', 'bl', 'br'].forEach(c => {
            const div = document.createElement('div');
            div.className = `qr-corner ${c}`;
            qrFrameInner.appendChild(div);
        });
        const overlay = document.createElement('div');
        overlay.id = 'expiredOverlay';
        overlay.className = 'qr-expired-overlay';
        overlay.innerHTML = '<div style=\"font-size:36px\">⏰</div><h3>Código Expirado</h3><p>Genera un nuevo código<br>para continuar</p>';
        qrFrameInner.appendChild(overlay);
    }

    function startTimer() {
        clearInterval(timerInterval);
        timeLeft = DURATION;
        updateTimerUI();
        timerInterval = setInterval(() => {
            timeLeft--;
            updateTimerUI();
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                const overlay = document.getElementById('expiredOverlay');
                if (overlay) overlay.classList.add('show');
            }
        }, 1000);
    }

    function updateTimerUI() {
        if (!timerDisplay) return;
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (ringFill) {
            const offset = 283 * (1 - (timeLeft / DURATION));
            ringFill.style.strokeDashoffset = offset;
            ringFill.style.stroke = timeLeft < 30 ? '#e8445a' : (timeLeft < 60 ? '#f5a623' : '#00d4a0');
        }

        if (timerBar) {
            timerBar.style.width = `${(timeLeft / DURATION) * 100}%`;
            timerBar.style.backgroundColor = timeLeft < 30 ? '#e8445a' : (timeLeft < 60 ? '#f5a623' : '#00d4a0');
        }
    }

    window.regenerar = function() {
        const overlay = document.getElementById('expiredOverlay');
        if (overlay) overlay.classList.remove('show');
        generateSessionCode();
        startTimer();
        renderQR();
        startPolling(); // Reiniciar polling con nuevo código
    };

    window.copiarLink = function() {
        const sessionId = codigoSesionEl ? codigoSesionEl.textContent.replace('#', '') : 'TEMP';
        const url = `${window.location.origin}/asistencia/registrar/${sessionId}`;
        navigator.clipboard.writeText(url).then(() => {
            alert('Enlace de asistencia copiado al portapapeles');
        });
    };

    function startPolling() {
        clearInterval(pollingInterval);
        fetchAttendance(); // Carga inicial
        pollingInterval = setInterval(fetchAttendance, 3000); // Polling cada 3 segundos
    }

    function fetchAttendance() {
        const sessionId = codigoSesionEl ? codigoSesionEl.textContent.replace('#', '') : null;
        if (!sessionId) return;

        fetch(`/asistencia/obtener/${sessionId}/`)
            .then(response => response.json())
            .then(data => {
                updateScannedList(data.asistencias);
            })
            .catch(err => console.error('Error fetching attendance:', err));
    }

    function updateScannedList(asistencias) {
        if (!scannedList) return;
        
        // Si no hay asistencias, mostrar estado vacío
        if (asistencias.length === 0) {
            scannedList.innerHTML = `
                <div class="empty-state">
                    <div style="font-size:32px;margin-bottom:8px">📱</div>
                    <div>Esperando escaneos reales...</div>
                </div>`;
            escaneados = 0;
        } else {
            scannedList.innerHTML = '';
            escaneados = asistencias.length;
            
            const colors = ['#3b74f5', '#00d4a0', '#f5a623', '#e8445a', '#6c5ce7'];
            
            asistencias.forEach(asis => {
                const item = document.createElement('div');
                item.className = 'scanned-item';
                const color = colors[Math.floor(Math.random() * colors.length)];
                item.innerHTML = `
                    <div class="scanned-avatar" style="background: ${color}">${asis.nombre.charAt(0)}</div>
                    <div class="scanned-name">${asis.nombre}</div>
                    <div class="scanned-time">${asis.hora}</div>
                    <div class="scanned-check">✓</div>`;
                scannedList.appendChild(item);
            });
        }

        if (escaneadosCountEl) escaneadosCountEl.textContent = escaneados;
        if (escaneadosLabelEl) escaneadosLabelEl.textContent = `${escaneados} / ${totalAlumnos}`;
        if (pctCountEl) pctCountEl.textContent = `${Math.round((escaneados / totalAlumnos) * 100)}%`;
    }

    init();
});
