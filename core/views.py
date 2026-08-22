import uuid
import boto3
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


class PingView(APIView):
    """No-auth health check endpoint — used to wake the Render free-tier server."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'service': 'billway-api',
        })


class GenerateUploadUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_name = request.data.get('file_name', 'upload.jpg')
        content_type = request.data.get('content_type', 'image/jpeg')
        
        # Generate a unique key for the file
        ext = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        unique_name = f"{uuid.uuid4()}.{ext}"
        object_name = f"products/{unique_name}"

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.STORAGES['default']['OPTIONS']['access_key'],
            aws_secret_access_key=settings.STORAGES['default']['OPTIONS']['secret_key'],
            region_name=settings.STORAGES['default']['OPTIONS']['region_name'],
            endpoint_url=settings.STORAGES['default']['OPTIONS']['endpoint_url']
        )

        try:
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.STORAGES['default']['OPTIONS']['bucket_name'],
                    'Key': object_name,
                    'ContentType': content_type,
                },
                ExpiresIn=3600
            )
            
            # Construct the public URL
            public_url = f"{settings.MEDIA_URL}{object_name}"
            
            return Response({
                'upload_url': presigned_url,
                'public_url': public_url
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
