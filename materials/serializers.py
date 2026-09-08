from rest_framework import serializers

from materials.models import Course, Lesson, Subscription
from materials.validators import validate_youtube_url


class SubscriptionRequestSerializer(serializers.Serializer):
    """Описывает ID курса для переключения подписки."""

    course_id = serializers.IntegerField(min_value=1)


class SubscriptionResponseSerializer(serializers.Serializer):
    """Описывает сообщение о результате переключения подписки."""

    message = serializers.CharField()


class LessonSerializer(serializers.ModelSerializer):
    """Преобразует объекты урока в JSON и обратно."""

    video_url = serializers.URLField(
        required=False,
        allow_blank=True,
        validators=[validate_youtube_url],
    )

    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ("owner",)


class CourseSerializer(serializers.ModelSerializer):
    """Преобразует курс вместе с уроками и признаком подписки."""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_lessons_count(self, course) -> int:
        """Возвращает количество уроков, связанных с курсом."""
        return course.lessons.count()

    def get_is_subscribed(self, course) -> bool:
        """Проверяет подписку текущего пользователя на курс."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user,
            course=course,
        ).exists()

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "owner",
            "lessons_count",
            "lessons",
            "is_subscribed",
        )
        read_only_fields = ("owner",)
