from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from asset.serializers.uploads import (
    CompleteRequestSerializer,
    CompleteResponseSerializer,
    PresignRequestSerializer,
    PresignResponseSerializer,
)
from asset.services.uploads import complete_upload, create_presigned_upload


class UploadsViewSet(viewsets.ViewSet):
    """
    ViewSet for handling presigned upload flow.

    Endpoints:
        POST /asset/upload/presign/
        POST /asset/upload/complete/
    """

    @action(detail=False, methods=['post'], url_path='presign')
    def presign(self, request: Request) -> Response:
        serializer = PresignRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = create_presigned_upload(
            install_id=serializer.validated_data['install_id'],
            content_type=serializer.validated_data['content_type'],
            purpose=serializer.validated_data.get('purpose'),
        )

        response_serializer = PresignResponseSerializer(
            instance={
                'upload_session_id': result.upload_session_id,
                'asset_id': result.asset_id,
                'presigned_url': result.presigned_url,
                'storage_key': result.storage_key,
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='complete')
    def complete(self, request: Request) -> Response:
        serializer = CompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = complete_upload(
            upload_session_id=serializer.validated_data['upload_session_id'],
            asset_id=serializer.validated_data['asset_id'],
            captured_at=serializer.validated_data.get('captured_at'),
        )

        response_serializer = CompleteResponseSerializer(
            instance={
                'upload_session_id': result.upload_session_id,
                'asset_id': result.asset_id,
                'hand_id': result.hand_id,
                'asset_ref_id': result.asset_ref_id,
            },
        )

        return Response(response_serializer.data, status=status.HTTP_200_OK)
