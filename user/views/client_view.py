from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from user.serializers import (
    ClientResponseSerializer,
    IdentifyRequestSerializer,
)
from user.services import delete_client, get_client, identify_client


INSTALL_ID_HEADER = 'HTTP_X_INSTALL_ID'


class ClientsViewSet(viewsets.ViewSet):
    """
    ViewSet for client identity management.

    Endpoints:
        POST /user/client/identify/
        GET /user/client/me/
        DELETE /user/client/me/
    """

    @action(detail=False, methods=['post'], url_path='identify')
    def identify(self, request: Request) -> Response:
        """
        Get or create a client by install_id.
        Updates last_seen_at if client exists.
        """
        serializer = IdentifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = identify_client(
            install_id=serializer.validated_data['install_id'],
            label=serializer.validated_data.get('label', ''),
        )

        response_serializer = ClientResponseSerializer(instance=client)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'delete'], url_path='me')
    def me(self, request: Request) -> Response:
        """
        Get or delete the current client identified by X-Install-Id header.
        """
        install_id = request.META.get(INSTALL_ID_HEADER)
        if not install_id:
            return Response(
                {'error': 'X-Install-Id header is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'GET':
            client = get_client(install_id=install_id)
            response_serializer = ClientResponseSerializer(instance=client)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        elif request.method == 'DELETE':
            delete_client(install_id=install_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
