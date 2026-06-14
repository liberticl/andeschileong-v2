from rest_framework import serializers
from .models import TrafficCount
import arrow


class TrafficCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficCount
        fields = (
            'datetime',
            'car_count', 'person_count', 'bicycle_count',
            'motorcycle_count', 'truck_count', 'bus_count'
        )

    def validate(self, data):
        """
        Garantiza que el campo datetime esté siempre presente y los demás
        campos numéricos se inicialicen a cero si faltan.
        """

        if 'datetime' not in data:
            raise serializers.ValidationError(
                {"datetime": "Este campo es obligatorio."})

        count_fields = [
            'car_count', 'person_count', 'bicycle_count',
            'motorcycle_count', 'truck_count', 'bus_count'
        ]

        qty = 0
        for field in count_fields:
            if field not in data:
                data[field] = 0
                qty += 1
            elif data[field] == 0:
                qty += 1

        if qty == len(count_fields):
            raise serializers.ValidationError(
                {
                    "count": "Al menos un campo debe ser mayor a cero.",
                    "fields": count_fields
                })

        return data

    def create(self, validated_data):
        device = self.context['request'].user
        return TrafficCount.objects.create(
            device=device,
            created_datetime=arrow.now().isoformat(),
            **validated_data
        )
