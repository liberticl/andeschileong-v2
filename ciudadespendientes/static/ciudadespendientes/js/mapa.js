document.addEventListener('DOMContentLoaded', function () {
    // IDs de las capas y sus checkboxes correspondientes
    const layerControls = {
        'green': 'toggle-green',
        'orange': 'toggle-orange',
        'red': 'toggle-red'
    };

    // Añade evento a cada checkbox
    Object.keys(layerControls).forEach(layerId => {
        const checkbox = document.getElementById(layerControls[layerId]);
        if (checkbox) {
            checkbox.addEventListener('change', function () {
                toggleLayer(layerId, this.checked);
            });
        }
    });

    // Función para activar/desactivar capas preservando los tooltips (usando .clone())
    function toggleLayer(layerId, isVisible) {
        if (!deckInstance) {
            console.error("deckInstance no está disponible");
            return;
        }

        const newLayers = deckInstance.props.layers.map(layer => {
            if (layer.id === layerId) {
                return layer.clone({ visible: isVisible });
            }
            return layer;
        });

        deckInstance.setProps({ layers: newLayers });
    }
});
