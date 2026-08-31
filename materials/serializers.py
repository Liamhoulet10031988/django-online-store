from rest_framework import serializers

from materials.models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    """Преобразует объекты курса в JSON и обратно."""

    class Meta:
        model = Course
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    """Преобразует объекты урока в JSON и обратно."""

    class Meta:
        model = Lesson
        fields = "__all__"
