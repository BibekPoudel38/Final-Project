from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = [
            "password",
        ]

    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            if User.objects.filter(email=email).exists():
                user = authenticate(email=email, password=password)

                if not user:
                    raise serializers.ValidationError(
                        {
                            "message": "Access denied. email no or password didn't match",
                        }
                    )

            else:
                raise serializers.ValidationError(
                    {
                        "message": "User with the email doesnot exist",
                    }
                )
        attrs["user"] = user
        return attrs


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password"]
        extra_kwargs = {
            "password": {
                "write_only": True,
            }
        }

    def create(self, validated_data, *args):
        if User.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError(
                {"error": "The email number is already in use"}
            )
        else:
            user = User(
                email=validated_data["email"],
            )
            password = validated_data["password"]
            user.set_password(password)
            user.save()
            return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "password": {
                "write_only": True,
            }
        }


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
    )

    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["password", "old_password"]

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError({"error": "Old password is not correct"})
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()
        return instance
