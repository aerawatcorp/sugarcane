from shortuuidfield import ShortUUIDField
from django.db import models


class BaseModel(models.Model):
    """
    Base model for possibly every other model.
    """

    idx = ShortUUIDField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_obsolete = models.BooleanField(default=False)
    meta = models.JSONField(default=dict, blank=True)

    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save()
        return self

    @classmethod
    def new(cls, **kwargs):
        return cls.objects.create(**kwargs)

    def delete(self, force_delete=True, **kwargs):
        if force_delete:
            super(BaseModel, self).delete(**kwargs)
        else:
            self.update(is_obsolete=True)
            return self

    class Meta:
        abstract = True
