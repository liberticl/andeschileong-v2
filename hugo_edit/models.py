import os
from django.db import models
from django.conf import settings
from django.utils.text import slugify

from .tasks import rebuild_hugo


class Activity(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", help_text="Resumen o bajada de la actividad")
    date = models.DateField("Fecha", blank=False, null=False)
    featured_image = models.CharField(
        "Ruta a Imagen Destacada", max_length=255, blank=True, help_text="Ej: /img/fotos/mi-foto.jpg")
    tags = models.CharField("Tags", max_length=255,
                            blank=True, help_text="Separados por comas")
    is_published = models.BooleanField("Publicado", default=False)
    is_deleted = models.BooleanField("Eliminado", default=False)
    content = models.TextField(
        "Contenido", help_text="Cuerpo de la actividad en formato Markdown")

    class Meta:
        verbose_name = "Actividad (Hugo)"
        verbose_name_plural = "Actividades (Hugo)"

    def __str__(self):
        return self.title

    def _hugo_path(self):
        year = self.date.year
        slug = slugify(self.title)
        return os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'actividades',
            str(year), f"{slug}.md")

    def generate_markdown(self):
        hugo_dir = os.path.dirname(self._hugo_path())
        os.makedirs(hugo_dir, exist_ok=True)

        tags_list = [
            f'"{t.strip()}"' for t in self.tags.split(',') if t.strip()]
        tags_str = "[" + ", ".join(tags_list) + "]"

        draft_line = "draft: true\n" if not self.is_published else ""

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
description: "{self.description}"
featured_image: "{self.featured_image}"
tags: {tags_str}
title: "{self.title}"
{draft_line}---

{self.content}
"""
        with open(self._hugo_path(), 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def remove_hugo_file(self):
        path = self._hugo_path()
        if os.path.exists(path):
            os.remove(path)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()
        rebuild_hugo.delay()

    def soft_delete(self):
        self.is_deleted = True
        self.save()
        self.remove_hugo_file()
        rebuild_hugo.delay()

    def restore(self):
        self.is_deleted = False
        self.save()


class Noticia(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", blank=True, help_text="Resumen o bajada (opcional)")
    date = models.DateField("Fecha")
    tags = models.CharField("Tags", max_length=255, blank=True,
                            help_text="Separados por comas")
    is_published = models.BooleanField("Publicado", default=False)
    is_deleted = models.BooleanField("Eliminado", default=False)
    content = models.TextField(
        "Contenido", help_text="Cuerpo de la noticia en formato Markdown")

    class Meta:
        verbose_name = "Noticia (Hugo)"
        verbose_name_plural = "Noticias (Hugo)"
        ordering = ['-date']

    def __str__(self):
        return self.title

    def _hugo_path(self):
        year = self.date.year
        slug = slugify(self.title)
        return os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'noticias',
            str(year), f"{slug}.md")

    def generate_markdown(self):
        hugo_dir = os.path.dirname(self._hugo_path())
        os.makedirs(hugo_dir, exist_ok=True)

        tags_list = [
            f'"{t.strip()}"' for t in self.tags.split(',') if t.strip()]
        tags_str = "[" + ", ".join(tags_list) + "]"

        draft_line = "draft: true\n" if not self.is_published else ""

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
tags: {tags_str}
title: "{self.title}"
{draft_line}---

{self.content}
"""
        with open(self._hugo_path(), 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def remove_hugo_file(self):
        path = self._hugo_path()
        if os.path.exists(path):
            os.remove(path)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()
        rebuild_hugo.delay()

    def soft_delete(self):
        self.is_deleted = True
        self.save()
        self.remove_hugo_file()
        rebuild_hugo.delay()

    def restore(self):
        self.is_deleted = False
        self.save()


class Estudio(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", blank=True, help_text="Resumen o bajada (opcional)")
    date = models.DateField("Fecha")
    featured_image = models.CharField(
        "Ruta a Imagen Destacada", max_length=255, blank=True,
        help_text="Ej: /img/estudios/2023/imagen.png")
    is_published = models.BooleanField("Publicado", default=False)
    is_deleted = models.BooleanField("Eliminado", default=False)
    content = models.TextField(
        "Contenido", help_text="Cuerpo del estudio en formato Markdown")

    class Meta:
        verbose_name = "Estudio (Hugo)"
        verbose_name_plural = "Estudios (Hugo)"
        ordering = ['-date']

    def __str__(self):
        return self.title

    def _hugo_path(self):
        year = self.date.year
        slug = slugify(self.title)
        return os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'estudios',
            str(year), f"{slug}.md")

    def generate_markdown(self):
        hugo_dir = os.path.dirname(self._hugo_path())
        os.makedirs(hugo_dir, exist_ok=True)

        draft_line = "draft: true\n" if not self.is_published else ""

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
description: "{self.description}"
featured_image: "{self.featured_image}"
title: "{self.title}"
{draft_line}---

{self.content}
"""
        with open(self._hugo_path(), 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def remove_hugo_file(self):
        path = self._hugo_path()
        if os.path.exists(path):
            os.remove(path)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()
        rebuild_hugo.delay()

    def soft_delete(self):
        self.is_deleted = True
        self.save()
        self.remove_hugo_file()
        rebuild_hugo.delay()

    def restore(self):
        self.is_deleted = False
        self.save()
