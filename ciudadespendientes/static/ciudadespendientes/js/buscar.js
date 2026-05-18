document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('buscar-form');
    const submitBtn = document.getElementById('submit-btn');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Get JSON data
    let zonesData = [];
    try {
        zonesData = JSON.parse(document.getElementById('zones-data').textContent);
    } catch (e) {
        console.error("Error cargando zonas:", e);
    }

    const paisSelect = document.getElementById('pais-select');
    const regionSelect = document.getElementById('region-select');
    const comunasContainer = document.getElementById('comunas-container');
    const anosContainer = document.getElementById('años-container');

    // Poblar países únicos
    const countries = [...new Set(zonesData.map(z => z.country).filter(c => c))];
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        paisSelect.appendChild(option);
    });

    paisSelect.addEventListener('change', function () {
        const selectedCountry = this.value;
        regionSelect.innerHTML = '<option value="">Seleccione una región</option>';
        comunasContainer.innerHTML = '<p class="text-muted small m-0">Seleccione una región primero.</p>';
        anosContainer.innerHTML = '<p class="text-muted small m-0">Seleccione comunas primero.</p>';

        regionSelect.disabled = true;
        comunasContainer.style.opacity = '0.5';
        comunasContainer.style.pointerEvents = 'none';
        anosContainer.style.opacity = '0.5';
        anosContainer.style.pointerEvents = 'none';
        validateForm();

        if (selectedCountry) {
            // Filtrar regiones usando el nuevo campo de atributos
            const countryZones = zonesData.filter(z => z.country === selectedCountry && z.region_name);
            const uniqueRegions = [...new Set(countryZones.map(z => z.region_name))];
            uniqueRegions.sort();

            uniqueRegions.forEach(regionName => {
                const option = document.createElement('option');
                option.value = regionName;
                option.textContent = regionName;
                regionSelect.appendChild(option);
            });
            regionSelect.disabled = false;
        }
    });

    regionSelect.addEventListener('change', function () {
        const selectedRegion = this.value;
        const selectedCountry = paisSelect.value;
        comunasContainer.innerHTML = '';
        anosContainer.innerHTML = '<p class="text-muted small m-0">Seleccione comunas primero.</p>';

        comunasContainer.style.opacity = '0.5';
        comunasContainer.style.pointerEvents = 'none';
        anosContainer.style.opacity = '0.5';
        anosContainer.style.pointerEvents = 'none';
        validateForm();

        if (selectedRegion) {
            comunasContainer.style.opacity = '1';
            comunasContainer.style.pointerEvents = 'auto';

            // Comunas filtradas ahora por su región asignada usando la llave foránea
            const comunas = zonesData.filter(z => z.region_name === selectedRegion && z.type !== 'País');

            if (comunas.length === 0) {
                comunasContainer.innerHTML = '<p class="text-muted small m-0">No hay comunas.</p>';
            }

            comunas.forEach((comuna, index) => {
                const div = document.createElement('div');
                div.className = 'form-check';
                div.style.marginBottom = '5px';

                const input = document.createElement('input');
                input.type = 'checkbox';
                input.id = 'ciudad' + index;
                input.name = 'comunas';
                input.value = comuna.name;
                input.className = 'form-check-input comuna-checkbox';
                input.style.cursor = 'pointer';
                input.dataset.years = JSON.stringify(comuna.available_years || []);

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = 'ciudad' + index;
                label.style.cursor = 'pointer';
                label.textContent = comuna.name.toUpperCase();

                div.appendChild(input);
                div.appendChild(label);
                comunasContainer.appendChild(div);

                input.addEventListener('change', updateYears);
            });
        }
    });

    function updateYears() {
        const selectedCheckboxes = document.querySelectorAll('.comuna-checkbox:checked');
        anosContainer.innerHTML = '';

        if (selectedCheckboxes.length === 0) {
            anosContainer.style.opacity = '0.5';
            anosContainer.style.pointerEvents = 'none';
            anosContainer.innerHTML = '<p class="text-muted small m-0">Seleccione comunas primero.</p>';
            validateForm();
            return;
        }

        anosContainer.style.opacity = '1';
        anosContainer.style.pointerEvents = 'auto';

        const allYearsSet = new Set();
        selectedCheckboxes.forEach(cb => {
            const years = JSON.parse(cb.dataset.years || "[]");
            years.forEach(y => allYearsSet.add(y));
        });

        // Ordenamos los años disponibles extraídos del JSON
        const sortedYears = Array.from(allYearsSet).sort((a, b) => b - a);

        if (sortedYears.length === 0) {
            anosContainer.innerHTML = '<p class="text-muted small m-0">No hay años disponibles para estas comunas en la base de datos.</p>';
        }

        sortedYears.forEach((year, index) => {
            const div = document.createElement('div');
            div.className = 'form-check';
            div.style.marginBottom = '5px';

            const input = document.createElement('input');
            input.type = 'checkbox';
            input.id = 'per' + index;
            input.name = 'periodo';
            input.value = year;
            input.className = 'form-check-input periodo-checkbox';
            input.style.cursor = 'pointer';

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.htmlFor = 'per' + index;
            label.style.cursor = 'pointer';
            label.textContent = year;

            div.appendChild(input);
            div.appendChild(label);
            anosContainer.appendChild(div);

            input.addEventListener('change', validateForm);
        });

        validateForm();
    }

    function validateForm() {
        const comunaCheckboxes = document.querySelectorAll('.comuna-checkbox');
        const periodoCheckboxes = document.querySelectorAll('.periodo-checkbox');

        const hasComuna = Array.from(comunaCheckboxes).some(cb => cb.checked);
        const hasPeriodo = Array.from(periodoCheckboxes).some(cb => cb.checked);
        submitBtn.disabled = !(hasComuna && hasPeriodo);
    }

    form.addEventListener('submit', function () {
        if (!submitBtn.disabled) {
            loadingOverlay.style.display = 'flex';
        }
    });

    // Check for query params to pre-load state when returning from mapa.html
    const urlParams = new URLSearchParams(window.location.search);
    const preComunasStr = urlParams.get('comunas');
    const prePeriodoStr = urlParams.get('periodo');

    if (preComunasStr && prePeriodoStr) {
        const preComunas = preComunasStr.split(',');
        const prePeriodos = prePeriodoStr.split(',');

        if (preComunas.length > 0) {
            // Find first comuna to infer Country and Region
            const targetComuna = zonesData.find(z => z.name === preComunas[0]);
            if (targetComuna && targetComuna.country && targetComuna.region_name) {

                // 1. Select Country and trigger change to build region dropdown
                paisSelect.value = targetComuna.country;
                paisSelect.dispatchEvent(new Event('change'));

                // 2. Select Region and trigger change to build comuna checkboxes
                regionSelect.value = targetComuna.region_name;
                regionSelect.dispatchEvent(new Event('change'));

                // 3. Mark selected Comunas as checked
                const comunaCheckboxes = document.querySelectorAll('.comuna-checkbox');
                comunaCheckboxes.forEach(cb => {
                    if (preComunas.includes(cb.value)) {
                        cb.checked = true;
                    }
                });

                // 4. Force update on Years/Period checkboxes using the checked Comunas
                updateYears();

                // 5. Mark selected Periodos as checked
                const periodoCheckboxes = document.querySelectorAll('.periodo-checkbox');
                periodoCheckboxes.forEach(cb => {
                    // values in query string are strings, checkbox values are strings too
                    if (prePeriodos.includes(cb.value)) {
                        cb.checked = true;
                    }
                });

                validateForm();
            }
        }
    }

});
