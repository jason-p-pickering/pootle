# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.cache import caches
from django.utils.functional import cached_property

from pootle.core.delegate import serializers


class StoreSerializer(object):

    def __init__(self, store):
        self.store = store

    @property
    def project_serializers(self):
        proj_serializers = (
            self.store.translation_project.project.serializers
            or "")
        return [
            s.strip()
            for s
            in proj_serializers.split(",")
            if s]

    @property
    def pootle_path(self):
        return self.store.pootle_path

    @cached_property
    def max_unit_revision(self):
        return self.store.get_max_unit_revision()

    @cached_property
    def serializers(self):
        available_serializers = serializers.gather(
            self.store.__class__, instance=self.store)
        found_serializers = []
        for serializer in self.project_serializers:
            found_serializers.append(available_serializers[serializer])
        return found_serializers

    def tostring(self):
        storeclass = self.store.get_file_class()
        store = self.store.convert(storeclass)
        if hasattr(store, "updateheader"):
            # FIXME We need those headers on import
            # However some formats just don't support setting metadata
            store.updateheader(add=True, X_Pootle_Path=self.pootle_path)
            store.updateheader(add=True, X_Pootle_Revision=self.max_unit_revision)
        return str(store)

    def pipeline(self, data):
        if not self.serializers:
            return data
        for serializer in self.serializers:
            data = serializer(self, data).output
        return data

    def serialize(self):
        cache = caches["exports"]
        ret = cache.get(
            self.pootle_path,
            version=self.max_unit_revision)
        if not ret:
            ret = self.pipeline(self.tostring().decode("utf8"))
            cache.set(
                self.pootle_path,
                ret,
                version=self.max_unit_revision)
        return ret
