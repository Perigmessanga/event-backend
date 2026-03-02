from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class ContactView(APIView):
    
    permission_classes = [AllowAny]   # 👈 AJOUTE ÇA
       
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        message = request.data.get("message")

        # Ici tu peux envoyer email ou sauvegarder en base

        return Response(
            {"message": "Message envoyé avec succès"},
            status=status.HTTP_200_OK
        )
# Create your views here.
