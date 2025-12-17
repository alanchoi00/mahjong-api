from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from asset.serializers.uploads import CompleteResponseSerializer
from asset.services.uploads import complete_upload
from asset.views.upload_view import get_install_id


class AssetViewSet(viewsets.ViewSet):
    """
    ViewSet for asset-level operations.

    Endpoints:
        POST /asset/{asset_id}/upload/complete/
    """

    @action(detail=True, methods=['post'], url_path='upload/complete')
    def complete(self, request: Request, pk: str) -> Response:
        """Complete an upload by verifying file exists and updating metadata."""
        install_id = get_install_id(request)

        result = complete_upload(
            asset_id=pk,
            install_id=install_id,
        )

        response_serializer = CompleteResponseSerializer(
            instance={
                'upload_session_id': result.upload_session_id,
                'asset_id': result.asset_id,
                'is_active': result.is_active,
                'byte_size': result.byte_size,
                'checksum': result.checksum,
            },
        )

        return Response(response_serializer.data, status=status.HTTP_200_OK)
