from django.shortcuts import get_object_or_404
from datetime import date
import re
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cats.models import Cat
from .models import Clinic, HealthRecord
from .serializers import ClinicSerializer, HealthRecordSerializer


class HealthPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CatHealthRecords(APIView):
    permission_classes = (IsAuthenticated,)

    def get_cat(self, request, cat_id):
        return get_object_or_404(Cat, pk=cat_id, owner=request.user)

    def get(self, request, cat_id):
        cat = self.get_cat(request, cat_id)
        records = HealthRecord.objects.filter(cat=cat).select_related('clinic')
        kind = request.query_params.get('type')
        if kind:
            if kind not in (HealthRecord.VISIT, HealthRecord.PROCEDURE):
                return Response({'type': ['Допустимы visit и procedure.']},
                                status=status.HTTP_400_BAD_REQUEST)
            records = records.filter(record_type=kind)
        for param, lookup in (('date_from', 'date__gte'),
                              ('date_to', 'date__lte')):
            raw = request.query_params.get(param)
            if raw:
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
                        raise ValueError
                    date.fromisoformat(raw)
                except ValueError:
                    return Response({param: ['Используйте дату YYYY-MM-DD.']},
                                    status=status.HTTP_400_BAD_REQUEST)
                records = records.filter(**{lookup: raw})
        paginator = HealthPagination()
        page = paginator.paginate_queryset(records, request, view=self)
        return paginator.get_paginated_response(
            HealthRecordSerializer(page, many=True).data
        )

    def post(self, request, cat_id):
        cat = self.get_cat(request, cat_id)
        serializer = HealthRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cat=cat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HealthRecordDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get_record(self, request, pk):
        return get_object_or_404(HealthRecord.objects.select_related('cat', 'clinic'),
                                 pk=pk, cat__owner=request.user)

    def get(self, request, pk):
        return Response(HealthRecordSerializer(self.get_record(request, pk)).data)

    def patch(self, request, pk):
        record = self.get_record(request, pk)
        serializer = HealthRecordSerializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_record(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompleteHealthRecord(HealthRecordDetail):
    http_method_names = ('post', 'options', 'head')

    def post(self, request, pk):
        record = self.get_record(request, pk)
        serializer = HealthRecordSerializer(record,
                                            data={'status': HealthRecord.COMPLETED},
                                            partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class Clinics(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(ClinicSerializer(Clinic.objects.all().order_by('name'),
                                         many=True).data)

    def post(self, request):
        if not request.user.is_staff:
            return Response({'detail': 'Только администратор может добавить клинику.'},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = ClinicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
