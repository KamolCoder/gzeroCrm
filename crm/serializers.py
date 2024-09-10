from .models import Client, Order, Abonement
from rest_framework import serializers


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'telegram_id', 'name', 'surname', 'image', 'profession']

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.surname = validated_data.get('surname', instance.email)
        instance.image = validated_data.get('image', instance.image)
        instance.profession = validated_data.get('profession', instance.profession)

        instance.save()
        return instance


class AbonementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonement
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            'client',
            'product',
            'payment_status',
            'summa',
            'summa_with_discount',
            'order_start',
            'order_end',
            'hour',
            'created_at',
            'filial')
