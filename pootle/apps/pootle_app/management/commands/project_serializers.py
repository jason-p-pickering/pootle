# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import CommandError
from django.utils.translation import ugettext_lazy as _

from pootle.core.delegate import serializers, deserializers
from pootle_app.management.commands import PootleCommand
from pootle_project.models import Project
from pootle_store.models import Store


class Command(PootleCommand):
    help = "Update database stores from files."
    process_disabled_projects = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            'project',
            type=str,
            default="",
            nargs="?",
            help='Pootle project')
        parser.add_argument(
            '--list',
            action='store_true',
            dest='list',
            help="List available de/serializers")
        parser.add_argument(
            '--set-serializers',
            action='store',
            dest='serializers',
            help="Set serializers for project")
        parser.add_argument(
            '--set-deserializers',
            action='store',
            dest='deserializers',
            help="Set deserializers for project")
        parser.add_argument(
            '--clear-serializers',
            action='store_true',
            dest='clear_serializers',
            help="Clear serializers for project")
        parser.add_argument(
            '--clear-deserializers',
            action='store_true',
            dest='clear_deserializers',
            help="Clear deserializers for project")

    def handle_all(self, **options):
        if options["list"]:
            return self.print_serializers_list()
        has_setters = (
            options["serializers"]
            or options["deserializers"]
            or options["clear_serializers"]
            or options["clear_deserializers"])
        if has_setters and not options["project"]:
            raise CommandError(
                _("You must specify a project to set the serializers "
                  "or deserializers for"))
        if options["project"]:
            return self.handle_project(**options)
        for options["project"] in Project.objects.exclude(disabled=True):
            self.print_project_serialization(options["project"])

    def print_serializers_list(self):
        serials = serializers.gather(Store)
        if not serials.keys():
            self.stdout.write(
                "There are no serializers set up on your system")

        deserials = deserializers.gather(Store)
        if not deserials.keys():
            self.stdout.write(
                "There are no deserializers set up on your system")

        if serials.keys():
            heading = "Serializers"
            self.stdout.write("\n%s" % heading)
            self.stdout.write("-" * len(heading))
            for name, serializer in serials.items():
                self.stdout.write(
                    "{: <30} {: <25} ".format(name, serializer))
        if deserials.keys():
            heading = "Deserializers"
            self.stdout.write("\n%s" % heading)
            self.stdout.write("-" * len(heading))
            for name, deserializer in deserials.items():
                self.stdout.write(
                    "{: <30} {: <25} ".format(name, deserializer))

    def print_project_serialization(self, project):
        project_name = "Project: %s(%s)" % (project.name, project.code)
        self.stdout.write(project_name)
        self.stdout.write(
            "  local filetype: %s" % project.localfiletype)
        self.stdout.write(
            "  serializers: %s" % (project.serializers or ""))
        self.stdout.write(
            "  deserializers: %s" % (project.deserializers or ""))

    def validate_deserializers(self, deserializerstr):
        avail_deserials = deserializers.gather(Store).keys()
        deserials = [
            x.strip() for x in deserializerstr.split(",") if x.strip()]
        for deserial in deserials:
            if deserial not in avail_deserials:
                raise CommandError(
                    "Missing deserializer(%s): "
                    "This deserializer is not installed on your system" % deserial)
        return ",".join(deserials)

    def validate_serializers(self, serializerstr):
        avail_serials = serializers.gather(Store).keys()
        serials = [
            x.strip() for x in serializerstr.split(",") if x.strip()]
        for serial in serials:
            if serial not in avail_serials:
                raise CommandError(
                    "Missing serializer(%s): "
                    "This serializer is not installed on your system" % serial)
        return ",".join(serials)

    def set_project_serialization(self, project, serializerstr):
        serializerstr = self.validate_serializers(serializerstr)
        project.serializers = serializerstr
        project.save()
        self.stdout.write(
            "Project serializers set: %s %s"
            % (project.code, serializerstr))

    def set_project_deserialization(self, project, deserializerstr):
        deserializerstr = self.validate_deserializers(deserializerstr)
        project.deserializers = deserializerstr
        project.save()
        self.stdout.write(
            "Project deserializers set: %s %s"
            % (project.code, deserializerstr))

    def clear_project_serialization(self, project):
        project.serializers = ""
        project.save()
        self.stdout.write(
            "Project serializers cleared: %s"
            % project.code)

    def clear_project_deserialization(self, project):
        project.deserializers = ""
        project.save()
        self.stdout.write(
            "Project deserializers cleared: %s"
            % project.code)

    def handle_project(self, **options):
        try:
            project = Project.objects.get(
                code=options["project"])
        except Project.DoesNotExist:
            raise CommandError(
                _("Project ('%s') does not exist")
                % options["project"])
        has_setters = (
            options["serializers"]
            or options["deserializers"]
            or options["clear_serializers"]
            or options["clear_deserializers"])
        if not has_setters:
            return self.print_project_serialization(project)
        elif options["serializers"] or options["deserializers"]:
            if options["serializers"]:
                self.set_project_serialization(project, options["serializers"])
            if options["deserializers"]:
                self.set_project_deserialization(project, options["deserializers"])
        else:
            if options["clear_serializers"]:
                self.clear_project_serialization(project)
            if options["clear_deserializers"]:
                self.clear_project_deserialization(project)
