from rest_framework import serializers


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    owner_id = serializers.UUIDField(required=True)
