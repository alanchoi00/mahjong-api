from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from asset.serializers.uploads import (
    PresignRequestSerializer,
    PresignResponseSerializer,
)
from asset.services.uploads import create_presigned_upload

INSTALL_ID_HEADER = 'X-Install-Id'


def get_install_id(request: Request) -> str:
    """Extract install_id from X-Install-Id header."""
    install_id = request.headers.get(INSTALL_ID_HEADER)
    if not install_id:
        raise NotAuthenticated(
            detail=f'Missing required header: {INSTALL_ID_HEADER}',
        )
    return install_id


class UploadsViewSet(viewsets.ViewSet):
    """
    ViewSet for handling presigned upload flow.

    Endpoints:
        POST /asset/upload/presign/
    """

    @action(detail=False, methods=['post'], url_path='presign')
    def presign(self, request: Request) -> Response:
        install_id = get_install_id(request)

        serializer = PresignRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = create_presigned_upload(
            install_id=install_id,
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
