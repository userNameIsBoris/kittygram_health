from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import permission_classes

from .models import Cat
from .serializers import CatSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def cat_list(request):
    if request.method == 'POST':
        serializer = CatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    cats = Cat.objects.all()
    serializer = CatSerializer(cats, many=True)
    return Response(serializer.data)
