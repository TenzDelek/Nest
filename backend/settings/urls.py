"""OWASP Nest URL configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from apps.github.api.urls import router as github_router
from apps.owasp.api.urls import router as owasp_router
from apps.slack.apps import SlackConfig

router = routers.DefaultRouter()
router.registry.extend(github_router.registry)
router.registry.extend(owasp_router.registry)

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("a/", admin.site.urls),
]

if SlackConfig.app:
    from apps.slack.views import slack_events_handler

    urlpatterns += [
        path("integrations/slack/events/", slack_events_handler, name="slack-events-handler"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
