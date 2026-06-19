from rest_framework import serializers
from .models import TrafficCount
import arrow

COUNT_FIELDS = [
    'car_count', 'person_count', 'bicycle_count',
    'motorcycle_count', 'truck_count', 'bus_count',
    'skater_count', 'pet_count'
]


class TrafficCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficCount
        fields = ('datetime',) + tuple(COUNT_FIELDS)

    def validate(self, data):
        """
        Garantiza que el campo datetime esté siempre presente y los demás
        campos numéricos se inicialicen a cero si faltan.
        """

        if 'datetime' not in data:
            raise serializers.ValidationError(
                {"datetime": "Este campo es obligatorio."})

        qty = 0
        for field in COUNT_FIELDS:
            if field not in data:
                data[field] = 0
                qty += 1
            elif data[field] == 0:
                qty += 1

        if qty == len(COUNT_FIELDS):
            raise serializers.ValidationError(
                {
                    "count": "Al menos un campo debe ser mayor a cero.",
                    "fields": COUNT_FIELDS
                })

        return data

    def create(self, validated_data):
        device = self.context['request'].user
        return TrafficCount.objects.create(
            device=device,
            created_datetime=arrow.now().isoformat(),
            **validated_data
        )

    def to_representation(self, instance):
        """Return only non-zero count fields to minimise response payload."""
        ret = super().to_representation(instance)
        # Always keep datetime; strip count fields that are zero
        return {
            k: v for k, v in ret.items()
            if k == 'datetime' or (k in COUNT_FIELDS and v)
        }


class TrafficCountBatchSerializer(serializers.Serializer):
    """Accepts a list of TrafficCount records in a single request."""
    records = TrafficCountSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError(
                "El lote debe contener al menos un registro.")
        if len(value) > 100:
            raise serializers.ValidationError(
                "El lote no puede superar los 100 registros.")
        return value
