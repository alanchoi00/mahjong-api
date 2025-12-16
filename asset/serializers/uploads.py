from rest_framework import serializers

from asset.constants import ALLOWED_IMAGE_MIMES, UploadPurpose


class PresignRequestSerializer(serializers.Serializer):
    install_id = serializers.CharField(
        required=True,
        max_length=64,
        help_text='Client install ID',
    )
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


class CompleteRequestSerializer(serializers.Serializer):
    upload_session_id = serializers.UUIDField(
        required=True,
        help_text='Upload session ID from presign response',
    )
    asset_id = serializers.UUIDField(
        required=True,
        help_text='Asset ID from presign response',
    )
    captured_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text='Device capture time (optional)',
    )


class CompleteResponseSerializer(serializers.Serializer):
    upload_session_id = serializers.UUIDField()
    asset_id = serializers.UUIDField()
    hand_id = serializers.UUIDField()
    asset_ref_id = serializers.UUIDField()
