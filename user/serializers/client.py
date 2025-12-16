from rest_framework import serializers


class IdentifyRequestSerializer(serializers.Serializer):
    install_id = serializers.CharField(
        required=True,
        max_length=64,
        help_text='Unique device/app install identifier',
    )
    label = serializers.CharField(
        required=False,
        max_length=120,
        default='',
        allow_blank=True,
        help_text='Optional device label/name',
    )


class ClientResponseSerializer(serializers.Serializer):
    install_id = serializers.CharField()
    label = serializers.CharField()
    created_at = serializers.DateTimeField()
    last_seen_at = serializers.DateTimeField()
