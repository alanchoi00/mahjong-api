from rest_framework import serializers

from asset.constants import ALLOWED_IMAGE_MIMES, UploadPurpose


class PresignRequestSerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(
        required=True,
        choices=[(m, m) for m in sorted(ALLOWED_IMAGE_MIMES)],
        help_text='MIME type of the file to upload',
    )
    purpose = serializers.ChoiceField(
        required=False,
        choices=UploadPurpose.choices(),
        default=UploadPurpose.HAND_PHOTO.value,
        help_text='Purpose of the upload',
    )


class PresignResponseSerializer(serializers.Serializer):
    upload_session_id = serializers.UUIDField()
    asset_id = serializers.UUIDField()
    presigned_url = serializers.URLField()
    storage_key = serializers.CharField()


class CompleteResponseSerializer(serializers.Serializer):
    """Response after completing an upload (no Hand/AssetRef creation)."""

    upload_session_id = serializers.UUIDField()
    asset_id = serializers.UUIDField()
    is_active = serializers.BooleanField()
    byte_size = serializers.IntegerField()
    checksum = serializers.CharField(allow_null=True)
