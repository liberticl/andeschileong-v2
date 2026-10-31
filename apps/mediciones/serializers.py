from rest_framework import serializers
from .models import TrafficCount
import arrow


COUNT_FIELDS = list(TrafficCount.COUNT_FIELDS)
SHORT_TO_COUNT = {
    'car': 'car_count',
    'person': 'person_count',
    'bicycle': 'bicycle_count',
    'motorcycle': 'motorcycle_count',
    'truck': 'truck_count',
    'bus': 'bus_count',
    'skater': 'skater_count',
    'pet': 'pet_count',
}
COUNT_TO_SHORT = {v: k for k, v in SHORT_TO_COUNT.items()}
DIRECTIONS = ('a_to_b', 'b_to_a')


def _direction_attr(count_field, direction):
    return f"{count_field[:-len('_count')]}_{direction}"


class TrafficCountSerializer(serializers.ModelSerializer):
    """
    Acepta (todo opcional salvo ``datetime``):
    - totales planos: ``car_count`` ... ``pet_count`` (backward-compatible),
    - línea anidada: ``line: {x1,y1,x2,y2} | null`` o plana
      ``line_x1..line_y2`` (coords normalizadas 0-1, A=start, B=end),
    - nombres de referencia: ``side_names: {a, b}`` o planos
      ``side_a_name`` / ``side_b_name`` (máx 100, opcionales),
    - direccionales anidados: ``direction_counts: {a_to_b: {...}, b_to_a: {...}}``
      (claves ``*_count`` o cortas ``car/bicycle/...``) o planos
      ``car_a_to_b`` ... ``pet_b_to_a``.
    Responde siempre con totales + ``line`` + ``direction_counts`` + ``side_names``.
    """
    line = serializers.DictField(
        child=serializers.FloatField(), required=False, allow_null=True)
    direction_counts = serializers.DictField(required=False)
    side_names = serializers.DictField(required=False)
    created_datetime = serializers.DateTimeField(read_only=True)

    class Meta:
        model = TrafficCount
        fields = (
            'datetime', 'created_datetime',
            'car_count', 'person_count', 'bicycle_count',
            'motorcycle_count', 'truck_count', 'bus_count',
            'skater_count', 'pet_count',
            'line_x1', 'line_y1', 'line_x2', 'line_y2',
            'side_a_name', 'side_b_name',
            'car_a_to_b', 'car_b_to_a',
            'person_a_to_b', 'person_b_to_a',
            'bicycle_a_to_b', 'bicycle_b_to_a',
            'motorcycle_a_to_b', 'motorcycle_b_to_a',
            'truck_a_to_b', 'truck_b_to_a',
            'bus_a_to_b', 'bus_b_to_a',
            'skater_a_to_b', 'skater_b_to_a',
            'pet_a_to_b', 'pet_b_to_a',
            'line', 'direction_counts', 'side_names',
        )
        extra_kwargs = {
            'line_x1': {'required': False, 'allow_null': True},
            'line_y1': {'required': False, 'allow_null': True},
            'line_x2': {'required': False, 'allow_null': True},
            'line_y2': {'required': False, 'allow_null': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Contrato anidado: totales + line + direction_counts + side_names.
        data['line'] = instance.get_line_dict()
        data['direction_counts'] = instance.get_direction_counts_dict()
        data['side_names'] = {'a': instance.side_a_name or '', 'b': instance.side_b_name or ''}
        return data

    def validate(self, data):
        if 'datetime' not in data:
            raise serializers.ValidationError(
                {"datetime": "Este campo es obligatorio."})

        # --- Línea: forma anidada tiene prioridad sobre la plana ---
        line = data.pop('line', serializers.empty)
        if line is not serializers.empty:
            if line is None:
                for f in TrafficCount.LINE_FIELDS:
                    data[f] = None
            elif isinstance(line, dict):
                try:
                    coords = {k: float(line[k]) for k in ('x1', 'y1', 'x2', 'y2')}
                except (KeyError, TypeError, ValueError):
                    raise serializers.ValidationError(
                        {"line": "Debe ser {x1,y1,x2,y2} con números 0-1 o null."})
                for k, v in coords.items():
                    if not 0.0 <= v <= 1.0:
                        raise serializers.ValidationError(
                            {"line": f"{k} debe estar entre 0 y 1."})
                data['line_x1'], data['line_y1'] = coords['x1'], coords['y1']
                data['line_x2'], data['line_y2'] = coords['x2'], coords['y2']
            else:
                raise serializers.ValidationError(
                    {"line": "Debe ser {x1,y1,x2,y2} con números 0-1 o null."})

        for f in TrafficCount.LINE_FIELDS:
            if f in data and data[f] is not None:
                try:
                    v = float(data[f])
                except (TypeError, ValueError):
                    raise serializers.ValidationError({f: "Debe ser un número 0-1."})
                if not 0.0 <= v <= 1.0:
                    raise serializers.ValidationError({f: "Debe estar entre 0 y 1."})
                data[f] = v
            elif f not in data:
                data[f] = None

        line_vals = [data[f] for f in TrafficCount.LINE_FIELDS]
        if any(v is not None for v in line_vals) and not all(v is not None for v in line_vals):
            raise serializers.ValidationError(
                {"line": "Línea incompleta: se requieren x1,y1,x2,y2 o null."})

        # --- Nombres de lados: forma anidada -> campos planos ---
        side_names = data.pop('side_names', serializers.empty)
        if side_names is not serializers.empty:
            if side_names is None:
                side_names = {}
            if not isinstance(side_names, dict):
                raise serializers.ValidationError(
                    {"side_names": "Debe ser {a, b} con textos de máx 100."})
            for key, field in (('a', 'side_a_name'), ('b', 'side_b_name')):
                if key in side_names and side_names[key] is not None:
                    data[field] = side_names[key]
        for field in ('side_a_name', 'side_b_name'):
            if field not in data or data[field] is None:
                data[field] = ''
            else:
                data[field] = str(data[field]).strip()
                if len(data[field]) > 100:
                    raise serializers.ValidationError(
                        {field: "Máximo 100 caracteres."})

        # --- Direccionales: forma anidada -> campos planos ---
        nested = data.pop('direction_counts', serializers.empty)
        if nested is not serializers.empty:
            if not isinstance(nested, dict):
                raise serializers.ValidationError(
                    {"direction_counts": "Debe ser {a_to_b: {...}, b_to_a: {...}}."})
            for direction in DIRECTIONS:
                bucket = nested.get(direction, {})
                if bucket is None:
                    bucket = {}
                if not isinstance(bucket, dict):
                    raise serializers.ValidationError(
                        {f"direction_counts.{direction}": "Debe ser un objeto."})
                for key, value in bucket.items():
                    count_field = SHORT_TO_COUNT.get(key, key)
                    if count_field not in COUNT_FIELDS:
                        raise serializers.ValidationError(
                            {f"direction_counts.{direction}.{key}":
                             f"Categoría desconocida (usar {COUNT_FIELDS} o {sorted(SHORT_TO_COUNT)})"})
                    try:
                        ivalue = int(value)
                    except (TypeError, ValueError):
                        raise serializers.ValidationError(
                            {f"direction_counts.{direction}.{key}": "Debe ser entero ≥ 0."})
                    if ivalue < 0:
                        raise serializers.ValidationError(
                            {f"direction_counts.{direction}.{key}": "Debe ser entero ≥ 0."})
                    data[_direction_attr(count_field, direction)] = ivalue

        # --- Totales + direccionales: defaults, derivación y consistencia ---
        for field in COUNT_FIELDS:
            if field not in data or data[field] is None:
                data[field] = 0
            else:
                try:
                    data[field] = int(data[field])
                except (TypeError, ValueError):
                    raise serializers.ValidationError({field: "Debe ser entero ≥ 0."})
                if data[field] < 0:
                    raise serializers.ValidationError({field: "Debe ser entero ≥ 0."})
            base = field[:-len('_count')]
            for direction in DIRECTIONS:
                attr = f"{base}_{direction}"
                if attr not in data or data[attr] is None:
                    data[attr] = 0
                else:
                    try:
                        data[attr] = int(data[attr])
                    except (TypeError, ValueError):
                        raise serializers.ValidationError({attr: "Debe ser entero ≥ 0."})
                    if data[attr] < 0:
                        raise serializers.ValidationError({attr: "Debe ser entero ≥ 0."})

        for field in COUNT_FIELDS:
            base = field[:-len('_count')]
            a = data[f"{base}_a_to_b"]
            b = data[f"{base}_b_to_a"]
            total = data[field]
            if a + b > 0 and total == 0:
                data[field] = a + b  # deriva el total desde el desglose
            elif a + b > 0 and total != a + b:
                raise serializers.ValidationError(
                    {field: f"Total ({total}) ≠ A→B ({a}) + B→A ({b})."})

        qty_zero = sum(1 for f in COUNT_FIELDS if data[f] == 0)
        has_dir = any(
            data[f"{f[:-len('_count')]}_{d}"] > 0
            for f in COUNT_FIELDS for d in DIRECTIONS)
        if qty_zero == len(COUNT_FIELDS) and not has_dir:
            raise serializers.ValidationError(
                {
                    "count": "Al menos un campo debe ser mayor a cero.",
                    "fields": COUNT_FIELDS
                })

        if has_dir and not all(v is not None for v in line_vals):
            raise serializers.ValidationError(
                {"line": "La línea (x1,y1,x2,y2) es requerida cuando se envía direction_counts."})

        return data

    def create(self, validated_data):
        validated_data.pop('line', None)
        validated_data.pop('direction_counts', None)
        validated_data.pop('side_names', None)
        device = self.context['request'].user
        return TrafficCount.objects.create(
            device=device,
            created_datetime=arrow.now().isoformat(),
            **validated_data
        )
