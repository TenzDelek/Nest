"""Project app models."""

import re
from base64 import b64decode

import yaml
from django.db import models

from apps.common.models import TimestampedModel


class Project(TimestampedModel):
    """Project model."""

    class Meta:
        db_table = "projects"
        verbose_name_plural = "Projects"

    class ProjectLevel(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        INCUBATOR = "incubator", "Incubator"
        LAB = "lab", "Lab"
        PRODUCTION = "production", "Production"
        FLAGSHIP = "flagship", "Flagship"

    class ProjectType(models.TextChoices):
        CODE = "code", "Code"
        DOCUMENTATION = "documentation", "Documentation"
        UNKNOWN = "unknown", "Unknown"

    name = models.CharField(verbose_name="Name", max_length=100)
    key = models.CharField(verbose_name="Key", max_length=100, unique=True)
    description = models.CharField(verbose_name="Description", max_length=500, default="")

    level = models.CharField(
        verbose_name="Level", max_length=20, choices=ProjectLevel, default=ProjectLevel.UNKNOWN
    )
    type = models.CharField(
        verbose_name="Type", max_length=20, choices=ProjectType, default=ProjectType.UNKNOWN
    )

    tags = models.JSONField(verbose_name="Tags", default=list)

    owasp_repository = models.ForeignKey(
        "repository.Repository", on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        """Repository human readable representation."""
        return f"{self.name}"

    def from_github(self, gh_repository, repository):
        """Update instance based on GitHub repository data."""
        index_md = gh_repository.get_contents("index.md")
        if not index_md:
            return

        md_content = b64decode(index_md.content).decode()
        if not md_content:
            return

        yaml_content = re.search(r"^---\n(.*?)\n---", md_content, re.DOTALL)
        if not yaml_content:
            return

        project_metadata = yaml.safe_load(yaml_content.group(1))
        field_mapping = {
            "name": "title",
            "description": "pitch",
            "tags": "tags",
        }

        # Direct fields.
        for model_field, metadata_field in field_mapping.items():
            value = project_metadata.get(metadata_field)
            if value is not None:
                setattr(self, model_field, value)

        # Level.
        project_level = project_metadata.get("level")
        if project_level:
            level_mapping = {
                2: self.ProjectLevel.INCUBATOR,
                3: self.ProjectLevel.LAB,
                3.5: self.ProjectLevel.PRODUCTION,
                4: self.ProjectLevel.FLAGSHIP,
            }
            self.level = level_mapping.get(project_level, self.ProjectLevel.UNKNOWN)

        # Type.
        project_type = project_metadata.get("type")
        if project_type in {self.ProjectType.CODE, self.ProjectType.DOCUMENTATION}:
            self.type = project_type

        # FKs.
        self.owasp_repository = repository