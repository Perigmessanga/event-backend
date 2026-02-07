from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, OTPVerification


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'role', 'profile_picture', 'bio',
            'is_email_verified', 'is_phone_verified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'password', 'password_confirm']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        if len(data['password']) < 8:
            raise serializers.ValidationError({'password': 'Password must be at least 8 characters'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password')
        data['user'] = user
        return data


class LoginPhoneOTPSerializer(serializers.Serializer):
    """Serializer for phone-based OTP login"""
    
    phone = serializers.CharField(required=True)
    otp_code = serializers.CharField(max_length=6, required=False, allow_blank=True)
    
    def validate(self, data):
        phone = data.get('phone')
        otp_code = data.get('otp_code')
        
        try:
            user = CustomUser.objects.get(phone=phone)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Phone number not registered')
        
        if otp_code:
            # Verify OTP
            otp = OTPVerification.objects.filter(user=user, otp_type='phone').first()
            if not otp or otp.otp_code != otp_code:
                raise serializers.ValidationError('Invalid OTP')
        
        data['user'] = user
        return data


class TokenSerializer(serializers.Serializer):
    """Serializer for JWT tokens"""
    
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer()


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    
    refresh = serializers.CharField(required=True, write_only=True)
    access = serializers.CharField(read_only=True)
    
    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError('Invalid refresh token')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({'new_password': 'Password must be at least 8 characters'})
        return data
