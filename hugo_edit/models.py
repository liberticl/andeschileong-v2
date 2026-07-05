import subprocess
import os
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Activity(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", help_text="Resumen o bajada de la actividad")
    date = models.DateField("Fecha", blank=False, null=False)
    featured_image = models.CharField(
        "Ruta a Imagen Destacada", max_length=255, blank=True, help_text="Ej: /img/fotos/mi-foto.jpg")
    tags = models.CharField("Tags", max_length=255,
                            blank=True, help_text="Separados por comas")

    content = models.TextField(
        "Contenido", help_text="Cuerpo de la actividad en formato Markdown")

    class Meta:
        verbose_name = "Actividad (Hugo)"
        verbose_name_plural = "Actividades (Hugo)"

    def __str__(self):
        return self.title

    def generate_markdown(self):
        year = self.date.year
        slug = slugify(self.title)

        hugo_dir = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'actividades', str(year))
        os.makedirs(hugo_dir, exist_ok=True)
        file_path = os.path.join(hugo_dir, f"{slug}.md")

        tags_list = [
            f'"{t.strip()}"' for t in self.tags.split(',') if t.strip()]
        tags_str = "[" + ", ".join(tags_list) + "]"

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
description: "{self.description}"
featured_image: "{self.featured_image}"
tags: {tags_str}
title: "{self.title}"
---

{self.content}
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()

        # Reconstruir Hugo
        subprocess.run(
            ['hugo', '--minify'],
            cwd=os.path.join(settings.BASE_DIR, 'hugo_site')
        )

    def delete(self, *args, **kwargs):
        year = self.date.year
        slug = slugify(self.title)

        hugo_dir = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'actividades', str(year))
        file_path = os.path.join(hugo_dir, f"{slug}.md")
        if os.path.exists(file_path):
            os.remove(file_path)

        # Reconstruir Hugo
        subprocess.run(
            ['hugo', '--minify'],
            cwd=os.path.join(settings.BASE_DIR, 'hugo_site')
        )

        super().delete(*args, **kwargs)


def _rebuild_hugo():
    subprocess.run(
        ['hugo', '--minify'],
        cwd=os.path.join(settings.BASE_DIR, 'hugo_site')
    )


class Noticia(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", blank=True, help_text="Resumen o bajada (opcional)")
    date = models.DateField("Fecha")
    tags = models.CharField("Tags", max_length=255, blank=True,
                            help_text="Separados por comas")
    content = models.TextField(
        "Contenido", help_text="Cuerpo de la noticia en formato Markdown")

    class Meta:
        verbose_name = "Noticia (Hugo)"
        verbose_name_plural = "Noticias (Hugo)"
        ordering = ['-date']

    def __str__(self):
        return self.title

    def generate_markdown(self):
        year = self.date.year
        slug = slugify(self.title)

        hugo_dir = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'noticias', str(year))
        os.makedirs(hugo_dir, exist_ok=True)
        file_path = os.path.join(hugo_dir, f"{slug}.md")

        tags_list = [
            f'"{t.strip()}"' for t in self.tags.split(',') if t.strip()]
        tags_str = "[" + ", ".join(tags_list) + "]"

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
tags: {tags_str}
title: "{self.title}"
---

{self.content}
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()
        _rebuild_hugo()

    def delete(self, *args, **kwargs):
        year = self.date.year
        slug = slugify(self.title)
        file_path = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'noticias',
            str(year), f"{slug}.md")
        if os.path.exists(file_path):
            os.remove(file_path)
        _rebuild_hugo()
        super().delete(*args, **kwargs)


class Estudio(models.Model):
    title = models.CharField("Título", max_length=200)
    description = models.TextField(
        "Descripción", blank=True, help_text="Resumen o bajada (opcional)")
    date = models.DateField("Fecha")
    featured_image = models.CharField(
        "Ruta a Imagen Destacada", max_length=255, blank=True,
        help_text="Ej: /img/estudios/2023/imagen.png")
    content = models.TextField(
        "Contenido", help_text="Cuerpo del estudio en formato Markdown")

    class Meta:
        verbose_name = "Estudio (Hugo)"
        verbose_name_plural = "Estudios (Hugo)"
        ordering = ['-date']

    def __str__(self):
        return self.title

    def generate_markdown(self):
        year = self.date.year
        slug = slugify(self.title)

        hugo_dir = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'estudios', str(year))
        os.makedirs(hugo_dir, exist_ok=True)
        file_path = os.path.join(hugo_dir, f"{slug}.md")

        frontmatter = f"""---
date: {self.date.strftime('%Y-%m-%d')}
description: "{self.description}"
featured_image: "{self.featured_image}"
title: "{self.title}"
---

{self.content}
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_markdown()
        _rebuild_hugo()

    def delete(self, *args, **kwargs):
        year = self.date.year
        slug = slugify(self.title)
        file_path = os.path.join(
            settings.BASE_DIR, 'hugo_site', 'content', 'estudios',
            str(year), f"{slug}.md")
        if os.path.exists(file_path):
            os.remove(file_path)
        _rebuild_hugo()
        super().delete(*args, **kwargs)
