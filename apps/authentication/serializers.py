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
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True, default='')
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True, default='')
    phone = serializers.CharField(required=False, allow_blank=True, default='')
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'firstName', 'lastName', 'phone', 'password', 'password_confirm']
        extra_kwargs = {
            'firstName': {'required': False},
            'lastName': {'required': False},
            'phone': {'required': False},
            'username': {'required': False},
        }
    
    def validate_email(self, value):
        """Check if email already exists"""
        if CustomUser.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value.lower()
    
    def validate_phone(self, value):
        """Allow empty phones, validate non-empty"""
        if not value or value.strip() == '':
            return ''
        # Basic phone validation if provided
        if len(value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 6:
            raise serializers.ValidationError('Phone number must contain at least 6 digits')
        return value
    
    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        if len(data.get('password', '')) < 8:
            raise serializers.ValidationError({'password': 'Password must be at least 8 characters'})
        
        # Generate username from email if not provided
        if not data.get('username'):
            email = data.get('email', '')
            data['username'] = email.split('@')[0] if email else 'user'
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user manually to avoid issues with create_user
        user = CustomUser(
            email=validated_data.get('email'),
            username=validated_data.get('username'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            is_active=True,
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password')
        
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid email or password')
        
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive')
        
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
