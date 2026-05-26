function filtrar() {
    const input = document.getElementById('searchInput');
    const table = document.getElementById('tablaAlumnos');
    if (!input || !table) return;

    const term = input.value.trim().toLowerCase();
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}
